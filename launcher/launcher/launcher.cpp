#include "stdafx.h"

#include "LimitSingleInstance.h"

#define MAX_ARGS_LENGTH 260

DWORD LaunchTarget(const TCHAR *target, const TCHAR *arguments, const TCHAR *dir)
{
	STARTUPINFOW siStartupInfo;
    PROCESS_INFORMATION piProcessInfo;
    ZeroMemory(&siStartupInfo, sizeof(siStartupInfo));
    ZeroMemory(&piProcessInfo, sizeof(piProcessInfo));
    siStartupInfo.cb = sizeof(siStartupInfo); 

	TCHAR args[MAX_ARGS_LENGTH];
	ZeroMemory(args, sizeof(args));
	
	// Prepend target as a first argument
	size_t target_len = _tcslen(target);
	args[0] = _T('"');
	_tcscpy(args + 1, target);
	args[target_len + 1] = _T('"');
	args[target_len + 2] = _T(' ');
	_tcsncpy(args + target_len + 3, arguments, MAX_ARGS_LENGTH - target_len - 4);

	if (CreateProcess(target, args, NULL, NULL, TRUE, CREATE_NO_WINDOW,
			NULL, dir, &siStartupInfo, &piProcessInfo))
	{
		CloseHandle(piProcessInfo.hProcess);
		CloseHandle(piProcessInfo.hThread); 
		return 0;
	}
	
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
		CLimitSingleInstance limit(_T("__enso_portable__"));

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

	_tcscpy(exec_dir, python_path);

	SetEnvironmentVariable(_T("PYTHONPATH"), python_path);

	_tcscpy(point, _T("python\\pythonw.exe"));

	// Enso startup script path
	TCHAR enso_executable_path[MAX_PATH];
	lstrcpyn(enso_executable_path, module_name, module_name_len);

	point = _tcsrchr(enso_executable_path, _T('\\'));
	_tcscpy(point + 1, _T("scripts\\run_enso.py"));

	if (_tcsstr(lpCmdLine, _T("--portable")))
	{
		SetEnvironmentVariable(_T("HOME"), exec_dir);
	}

    return LaunchTarget(python_path, enso_executable_path, exec_dir);
}