# main.py
import os

def define_env(env):
    """
    To jest funkcja hooka dla mkdocs-macros-plugin.
    """

    @env.macro
    def project_tree():
        """
        Generuje drzewo katalogów projektu jako sformatowany blok kodu Markdown.
        """
        # Lista katalogów i plików do ignorowania
        ignore_dirs = {
            '.git', '.venv', 'venv', '__pycache__', '.idea', '.vscode', 
            'site', 'docs', 'media', 'migrations'
        }
        ignore_files = {
            'db.sqlite3', '.gitignore', 'mkdocs.yml', 'main.py', 
            'poetry.lock', 'pyproject.toml'
        }
        
        # Zaczynamy od katalogu bieżącego
        startpath = '.'
        structure = []

        for root, dirs, files in os.walk(startpath):
            # Modyfikacja listy dirs in-place, aby pominąć ignorowane katalogi
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            level = root.replace(startpath, '').count(os.sep)
            indent = '│   ' * (level - 1) + '├── ' if level > 0 else ''
            
            if level == 0:
                structure.append("projektgrupowy/")
            else:
                dirname = os.path.basename(root)
                structure.append(f'{indent}{dirname}/')

            subindent = '│   ' * level + '├── '
            
            for f in files:
                if f not in ignore_files and not f.endswith('.pyc'):
                    structure.append(f'{subindent}{f}')

        # Zwracamy wynik w bloku kodu (code block)
        return "```text\n" + "\n".join(structure) + "\n```"