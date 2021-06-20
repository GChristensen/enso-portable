#include "stdafx.h"

#include "LimitSingleInstance.h"

#define MAX_ARGS_LENGTH 1000

DWORD LaunchTarget(const TCHAR *target, const TCHAR *arguments, const TCHAR *dir)
{
	STARTUPINFOW siStartupInfo;
    PROCESS_INFORMATION piProcessInfo;
    ZeroMemory(&siStartupInfo, sizeof(siStartupInfo));
    ZeroMemory(&piProcessInfo, sizeof(piProcessInfo));
    siStartupInfo.cb = sizeof(siStartupInfo); 

	TCHAR args[MAX_ARGS_LENGTH];
	ZeroMemory(args, sizeof(args));

	//size_t target_len = _tcslen(target);
	size_t args_len = _tcslen(arguments);

	if (/*target_len + */args_len >= MAX_ARGS_LENGTH - 10)
		return 0;

	args[0] = _T('"');
	_tcscpy(args + 1, arguments);
	args[args_len + 1] = _T('"');

	ShellExecute(NULL, _T("open"), target, args, NULL, 0);
	
	return 3;
}

int APIENTRY _tWinMain(HINSTANCE hInstance,
                     HINSTANCE hPrevInstance,
                     LPTSTR    lpCmdLine,
                     int       nCmdShow)
{
	if (_tcsstr(lpCmdLine, _T("--restart")))
	{
		TCHAR *stop, *spc = _tcsrchr(lpCmdLine, _T(' '));
		DWORD pid = _tcstoul(spc + 1, &stop, 10);

		HANDLE hproc = OpenProcess(SYNCHRONIZE, FALSE, pid);
		WaitForSingleObject(hproc, INFINITE);
		CloseHandle(hproc);
	}
	else
	{
		CLimitSingleInstance limit(_T("__enso_open_source__"));

		if (limit.IsAnotherInstanceRunning())
		{
			return 0;
		}
	}


	TCHAR *point = NULL;
	TCHAR module_name[MAX_PATH];
	GetModuleFileName(hInstance, module_name, MAX_PATH);

	size_t module_name_len = lstrlen(module_name);

	// Python path
	TCHAR python_path[MAX_PATH];
	TCHAR exec_dir[MAX_PATH];
	lstrcpyn(python_path, module_name, module_name_len);

	point = _tcsrchr(python_path, _T('\\'));
	*(++point) = NULL;

	size_t module_dir_len = lstrlen(python_path);

	_tcscpy_s(exec_dir, MAX_PATH, python_path);

	SetEnvironmentVariable(_T("PYTHONPATH"), python_path);

	if (!_tcsicmp(exec_dir, _T("C:\\Program Files\\Enso\\")))
		_tcscpy_s(point, MAX_PATH - module_dir_len - 1, _T("python\\pythonu.exe"));
	else
		_tcscpy_s(point, MAX_PATH - module_dir_len - 1, _T("python\\pythonw.exe"));

	// Enso startup script path
	TCHAR enso_executable_path[MAX_PATH];
	lstrcpyn(enso_executable_path, module_name, module_name_len);

	point = _tcsrchr(enso_executable_path, _T('\\'));
	_tcscpy_s(point + 1, MAX_PATH - module_dir_len - 1, _T("scripts\\run_enso.py"));

#ifndef PORTABLE
	if (_tcsstr(lpCmdLine, _T("--portable")))
	{
#endif
		point = _tcsrchr(exec_dir, _T('\\'));
		*point = NULL;

		SetEnvironmentVariable(_T("HOME"), exec_dir);
#ifndef PORTABLE
	}
#endif


    return LaunchTarget(python_path, enso_executable_path, exec_dir);
}