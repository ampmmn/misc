// 個人作業用のfd.exeのラッパー
// ショートカット(.lnk)先のフォルダパスを解決して、fd.exeに渡す--search-pathオプションとして追加することにより、
// ショートカット先のパスも検索対象として含めることができるようにする
// 
#include "pch.h"
#include "framework.h"
#include "fdp.h"
#include "Pipe.h"
#include "CharConverter.h"
#include <locale.h>
#include <deque>
#include <vector>

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

constexpr int MAX_PATH_NTFS = (32767+1);

CWinApp theApp;

/**
 	ショートカット(.lnk)のパスを解決する
 	@return 
 	@param[in]  linkPath     .lnkファイルのパス
 	@param[out] resolvedPath ショートカットのリンク先のパス
*/
static bool ResolveShortcutPath(
	const CString& linkPath,
	CString& resolvedPath
)
{
	CComPtr<IShellLink> shellLinkPtr;

	HRESULT hr =
		CoCreateInstance(CLSID_ShellLink, NULL, CLSCTX_INPROC_SERVER,
		                 IID_IShellLink, (void**) &shellLinkPtr);

	if (FAILED(hr)){
		return false;
	}

	CComPtr<IPersistFile> persistFilePtr;
	hr = shellLinkPtr->QueryInterface(IID_IPersistFile, (void**)&persistFilePtr);
	if (FAILED(hr)) {
		return false;
	}

	hr = persistFilePtr->Load(linkPath, STGM_READ);
	if (FAILED(hr)) {
		return false;
	}

	wchar_t pathWideChar[MAX_PATH_NTFS];

	WIN32_FIND_DATA wfd;
	shellLinkPtr->GetPath(pathWideChar, MAX_PATH_NTFS, &wfd, 0);

	CString path((CStringW)pathWideChar);
	resolvedPath = path;

	return true;
}


static void FindShortcutResolvedDirs(LPCTSTR initDir, std::vector<CString>& dirs)
{
	std::deque<CString> targetDirs;
	targetDirs.push_back(initDir);

	while (targetDirs.empty() == false) {

		CString targetDir = targetDirs.front();
		targetDirs.pop_front();

		CFileFind fnd;

		TCHAR pattern[MAX_PATH_NTFS];
		_tcscpy_s(pattern, targetDir);
		PathAppend(pattern, _T("*.*"));

		BOOL hasNext = fnd.FindFile(pattern, 0);
		while(hasNext) {

			hasNext = fnd.FindNextFile();

			if(fnd.IsDots()) {
				continue;
			}

			CString path = fnd.GetFilePath();

			// フォルダだった場合は次のラウンドで処理をするので対象リストに登録しておく
			if(fnd.IsDirectory()) {
				targetDirs.push_back(path);
				continue;
			}

			// ショートカットファイルでなければスキップ
			CString ext = PathFindExtension(path);
			if (ext.CompareNoCase(_T(".lnk")) != 0) {
				continue;
			}

			// ショートカットのパスを解決できない、ショートカット先がファイルの場合はスキップ
			CString resolvedPath;
			if (ResolveShortcutPath(path, resolvedPath) == false || PathIsDirectory(resolvedPath) == FALSE) {
				continue;
			}

			// ショートカット先のフォルダパスをにリストに追加
			dirs.push_back(resolvedPath);
		}

		fnd.Close();
	}
}

int _tmain(int argc, TCHAR* argv[])
{
#ifdef UNICODE
	_tsetlocale(LC_ALL, _T(""));
#endif
	CoInitialize(nullptr);

	// MFCの初期化
	if (!AfxWinInit(::GetModuleHandle(nullptr), nullptr, ::GetCommandLine(), 0)) {
		wprintf(L"Fatal Error: Failed to initliaze MFC.\n");
		return 1;
	}

	// カレントディレクトリ以下の.lnkパスを調べて、リンク先のフォルダ一覧を生成しておく
	std::vector<CString> resolvedDirs;
	FindShortcutResolvedDirs(_T("."), resolvedDirs);

	CString exePath(_T("fd.exe"));

	// 環境変数FDP_FD_PATHでfdのパスが指定されていた場合はそれを使う
	size_t len = 0;
	TCHAR fdUserPath[MAX_PATH_NTFS];
	_tgetenv_s(&len, fdUserPath, MAX_PATH_NTFS, _T("FDP_FD_PATH"));
	if (len != 0) {
		exePath = fdUserPath;
	}

	// カレントディレクトリとショートカットリンク先のディレクトリパスを
	// 検索対象とするコマンドライン文字列を生成しておく
	CString cmdline;
	cmdline += exePath;

	cmdline += _T(" --search-path .");
	for (auto& dirPath : resolvedDirs) {
		CString tmp;
		tmp.Format(_T(" --search-path \"%s\""), dirPath);
		cmdline += tmp;
	}

	// コマンドライン引数で与えられた文字列を、fdに渡すコマンドライン文字列として追記する
	for (int i = 1; i < argc; ++i) {
		cmdline += _T(" ");

		CString tok(argv[i]);
		if (tok.Find(_T(" ")) != -1) {
			cmdline += _T("\"");
			cmdline += tok;
			cmdline += _T("\"");
		}
		else {
			cmdline += tok;
		}
	}

	// 子プロセスの出力を受け取るためのパイプを作成する
	Pipe pipeForStdout;
	Pipe pipeForStderr;

	// fd.exeを起動する
	PROCESS_INFORMATION pi = {};

	STARTUPINFO si = {};
	si.cb = sizeof(si);
	si.dwFlags = STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
	si.hStdOutput = pipeForStdout.GetWriteHandle();
	si.hStdError = pipeForStderr.GetWriteHandle();
	si.wShowWindow = SW_HIDE;

	BOOL isOK = CreateProcess(nullptr, cmdline.GetBuffer(cmdline.GetLength()), NULL, NULL, TRUE, 0, NULL, nullptr, &si, &pi);
	cmdline.ReleaseBuffer();

	if (isOK == FALSE) {
		// 起動に失敗
		_ftprintf(stderr, _T("Failed to run fd [%s]\n"), (LPCTSTR)exePath);
		return 1;
	}

	CloseHandle(pi.hThread);

	// fdが出力したstdoutの出力を受け取り、自プロセスのstdoutに出力する
	HANDLE hRead = pipeForStdout.GetReadHandle();

	std::vector<char> output;
	std::vector<char> err;

	bool isExitChild = false;
	while(isExitChild == false) {

		if (isExitChild == false && WaitForSingleObject(pi.hProcess, 0) == WAIT_OBJECT_0) {
			isExitChild = true;

			DWORD exitCode;
			GetExitCodeProcess(pi.hProcess, &exitCode);

			if (exitCode != 0) {
				pipeForStderr.ReadAll(err);
				err.push_back(0x00);
				CloseHandle(pi.hProcess);

				// fdが出力したエラー出力を出力する
				CString dstErr;
				CharConverter conv;
				conv.Convert(&err.front(), dstErr);
				_ftprintf(stderr, _T("%s\n"), (LPCTSTR)dstErr);

				return exitCode;
			}
		}

		// FIXME: 今の形だと、fdの出力すべてをメモリ上にためる形になっているので、適宜stdoutにflushするつくりにしたい
		// (が、現状想定するユースケースでは今の実装方式で問題ない)
		pipeForStdout.ReadAll(output);
		pipeForStderr.ReadAll(err);
	}

	CloseHandle(pi.hProcess);
	output.push_back(0x00);
	err.push_back(0x00);

	CString dst;
	CharConverter conv;
	conv.Convert(&output.front(), dst);

	// 最後にfd.exeのstdout出力を出力する
	_tprintf(_T("%s\n"), (LPCTSTR)dst);

	return 0;
}
