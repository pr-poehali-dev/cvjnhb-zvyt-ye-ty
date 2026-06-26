import json
import os
import shutil
import glob as glob_module


BASE_DIR = '/tmp/workspace'


def ensure_base():
    os.makedirs(BASE_DIR, exist_ok=True)


def safe_path(path: str, cwd: str = BASE_DIR) -> str:
    if os.path.isabs(path):
        p = os.path.realpath(os.path.join(BASE_DIR, path.lstrip('/')))
    else:
        p = os.path.realpath(os.path.join(cwd, path))
    if not p.startswith(BASE_DIR):
        raise ValueError('Доступ запрещён: путь вне рабочей директории')
    return p


def cmd_ls(args: list, cwd: str) -> str:
    path = safe_path(args[0] if args else '.', cwd)
    if not os.path.exists(path):
        return f'ls: {args[0] if args else "."}: нет такого файла или директории'
    if os.path.isfile(path):
        return os.path.basename(path)
    items = sorted(os.listdir(path))
    if not items:
        return '(директория пуста)'
    lines = []
    for item in items:
        full = os.path.join(path, item)
        lines.append(item + '/' if os.path.isdir(full) else f'{item}  ({os.path.getsize(full)} байт)')
    return '\n'.join(lines)


def cmd_cat(args: list, cwd: str) -> str:
    if not args:
        return 'cat: укажи имя файла'
    path = safe_path(args[0], cwd)
    if not os.path.exists(path):
        return f'cat: {args[0]}: нет такого файла'
    if os.path.isdir(path):
        return f'cat: {args[0]}: это директория'
    with open(path, 'r', errors='replace') as f:
        return f.read()


def cmd_write(args: list, cwd: str) -> str:
    if not args:
        return 'write: укажи имя файла'
    path = safe_path(args[0], cwd)
    content = ' '.join(args[1:])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    return f'Файл записан: {args[0]}'


def cmd_append(args: list, cwd: str) -> str:
    if not args:
        return 'append: укажи имя файла'
    path = safe_path(args[0], cwd)
    content = ' '.join(args[1:])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a') as f:
        f.write(content + '\n')
    return f'Добавлено в файл: {args[0]}'


def cmd_mkdir(args: list, cwd: str) -> str:
    if not args:
        return 'mkdir: укажи имя директории'
    os.makedirs(safe_path(args[0], cwd), exist_ok=True)
    return f'Директория создана: {args[0]}'


def cmd_rm(args: list, cwd: str) -> str:
    if not args:
        return 'rm: укажи путь'
    path = safe_path(args[0], cwd)
    if not os.path.exists(path):
        return f'rm: {args[0]}: нет такого файла'
    if os.path.isdir(path):
        shutil.rmtree(path)
        return f'Директория удалена: {args[0]}'
    os.remove(path)
    return f'Файл удалён: {args[0]}'


def cmd_mv(args: list, cwd: str) -> str:
    if len(args) < 2:
        return 'mv: укажи источник и назначение'
    src, dst = safe_path(args[0], cwd), safe_path(args[1], cwd)
    if not os.path.exists(src):
        return f'mv: {args[0]}: нет такого файла'
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)
    return f'Перемещено: {args[0]} → {args[1]}'


def cmd_cp(args: list, cwd: str) -> str:
    if len(args) < 2:
        return 'cp: укажи источник и назначение'
    src, dst = safe_path(args[0], cwd), safe_path(args[1], cwd)
    if not os.path.exists(src):
        return f'cp: {args[0]}: нет такого файла'
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copytree(src, dst) if os.path.isdir(src) else shutil.copy2(src, dst)
    return f'Скопировано: {args[0]} → {args[1]}'


def cmd_find(args: list, cwd: str) -> str:
    pattern = args[0] if args else '*'
    matches = glob_module.glob(os.path.join(cwd, '**', pattern), recursive=True)
    if not matches:
        return '(ничего не найдено)'
    return '\n'.join(p.replace(BASE_DIR, '') for p in matches)


def cmd_size(args: list, cwd: str) -> str:
    path = safe_path(args[0] if args else '.', cwd)
    if os.path.isfile(path):
        return f'{os.path.getsize(path)} байт'
    total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(path) for f in fs)
    return f'{total} байт'


def cmd_run(args: list, cwd: str) -> str:
    if not args:
        return 'run: укажи имя файла (.py)'
    filename = args[0]
    if not filename.endswith('.py'):
        return 'run: поддерживаются только .py файлы'
    path = safe_path(filename, cwd)
    if not os.path.exists(path):
        return f'run: {filename}: нет такого файла'
    import io
    import sys
    import importlib.util
    import traceback
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = stdout_capture, stderr_capture
    exit_code = 0
    try:
        spec = importlib.util.spec_from_file_location('__main__', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except SystemExit as e:
        exit_code = e.code if isinstance(e.code, int) else 0
    except Exception:
        stderr_capture.write(traceback.format_exc())
        exit_code = 1
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
    out = stdout_capture.getvalue()
    err = stderr_capture.getvalue()
    return (out + err) or '(нет вывода)'


def cmd_pwd(args: list, cwd: str) -> str:
    return cwd.replace(BASE_DIR, '') or '/'


def cmd_help(args: list, cwd: str) -> str:
    return """\
Доступные команды:
  ls [путь]             — список файлов
  cat <файл>            — содержимое файла
  write <файл> <текст>  — записать текст в файл
  append <файл> <текст> — добавить строку в файл
  mkdir <папка>         — создать директорию
  rm <путь>             — удалить файл или папку
  mv <src> <dst>        — переместить
  cp <src> <dst>        — скопировать
  find [паттерн]        — найти файлы (например: find *.txt)
  size [путь]           — размер файла или папки
  run <файл.py>         — запустить Python-скрипт
  cd <папка>            — перейти в директорию
  pwd                   — текущая директория
  help                  — эта справка"""


COMMANDS = {
    'ls': cmd_ls, 'cat': cmd_cat, 'write': cmd_write, 'append': cmd_append,
    'mkdir': cmd_mkdir, 'rm': cmd_rm, 'mv': cmd_mv, 'cp': cmd_cp,
    'find': cmd_find, 'size': cmd_size, 'run': cmd_run,
    'pwd': cmd_pwd, 'help': cmd_help,
}


def handler(event: dict, context) -> dict:
    """Файловый терминал — команды для работы с файлами на сервере, поддержка cd"""
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type', 'Access-Control-Max-Age': '86400'}, 'body': ''}

    ensure_base()
    body = json.loads(event.get('body') or '{}')
    raw = body.get('command', '').strip()
    cwd_rel = body.get('cwd', '/')
    cwd = os.path.realpath(os.path.join(BASE_DIR, cwd_rel.lstrip('/')))
    if not cwd.startswith(BASE_DIR):
        cwd = BASE_DIR

    if not raw:
        return {'statusCode': 400, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': 'Команда не указана'})}

    parts = raw.split()
    cmd = parts[0].lower()
    args = parts[1:]

    new_cwd = cwd_rel

    if cmd == 'cd':
        if not args or args[0] in ('~', '/'):
            new_cwd = '/'
            output, exit_code = '', 0
        else:
            try:
                target = safe_path(args[0], cwd)
                if not os.path.exists(target):
                    output, exit_code = f'cd: {args[0]}: нет такой директории', 1
                elif not os.path.isdir(target):
                    output, exit_code = f'cd: {args[0]}: не является директорией', 1
                else:
                    new_cwd = target.replace(BASE_DIR, '') or '/'
                    output, exit_code = '', 0
            except ValueError as e:
                output, exit_code = str(e), 1
    elif cmd not in COMMANDS:
        output, exit_code = f'{cmd}: команда не найдена. Напечатай help для списка команд.', 127
    else:
        try:
            output, exit_code = COMMANDS[cmd](args, cwd), 0
        except ValueError as e:
            output, exit_code = str(e), 1
        except Exception as e:
            output, exit_code = f'Ошибка: {e}', 1

    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json'},
        'body': json.dumps({'output': output, 'exit_code': exit_code, 'cwd': new_cwd})
    }