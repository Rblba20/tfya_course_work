import re

# Определение типов токенов
TOKENS = [
    ('COMMENT', r'\{[^}]*?\}'),  # многострочные комментарии (обновлено для многострок)
    ('KEYWORD', r'\b(program|var|begin|end|integer|real|boolean|if|then|else|for|to|do|while|read|write|as)\b'),
    ('OP_REL', r'\b(NE|EQ|LT|LE|GT|GE)\b'),  # операции группы отношений
    ('BOOLEAN', r'\b(true|false)\b'),  # логические константы
    ('OP_ADD', r'\b(plus|min|or)\b'),  # операции группы сложения
    ('OP_MUL', r'\b(mult|div|and)\b'),  # операции группы умножения
    ('OP_UNARY', r'~'),  # унарная операция
    ('ID', r'\b[A-Za-z][A-Za-z0-9]*\b'),  # идентификаторы
    ('BIN', r'\b[01]+[Bb]\b'),  # двоичное число
    ('OCT', r'\b[0-7]+[Oo]\b'),  # восьмеричное число
    ('HEX', r'\b[0-9A-Fa-f]+[Hh]\b'),  # шестнадцатеричное число
    ('REAL', r'\b\d+\.\d+([Ee][+-]?\d+)?\b'),  # действительное число
    ('PUNCT', r'[;:.(),\[\]]'),  # знаки пунктуации
    ('INTEGER', r'\b\d+[Dd]?\b'),  # целое число (десятичное)
    ('WHITESPACE', r'\s+'),  # пробелы и переводы строк
    ('UNKNOWN', r'.'),  # неизвестные символы (обработка ошибок)
]

class Lexer:
    def __init__(self, code):
        self.code = code
        self.pos = 0
        self.tokens = []
        self.variables = set()  # Множество для хранения объявленных переменных
        self.in_var_section = False  # Флаг для определения, находимся ли мы в разделе объявления переменных

    def tokenize(self):
        while self.pos < len(self.code):
            match = None
            for token_type, regex in TOKENS:
                pattern = re.compile(regex, re.DOTALL)
                match = pattern.match(self.code, self.pos)
                if match:
                    text = match.group(0)
                    if token_type == 'WHITESPACE':
                        # Пропускаем пробелы
                        pass
                    elif token_type == 'KEYWORD' and text == 'var':
                        # Начинаем раздел объявлений переменных
                        self.in_var_section = True
                        self.tokens.append((token_type, text))
                    elif token_type == 'KEYWORD' and text in ['begin', 'end']:
                        # Конец раздела объявлений переменных
                        if text == 'begin':
                            self.in_var_section = False
                        self.tokens.append((token_type, text))
                    elif token_type == 'REAL':
                        float_value = float(match.group(0))
                        self.tokens.append((token_type, str(float_value)))
                    elif token_type == 'ID':
                        if self.in_var_section:
                            # Добавляем переменные в таблицу символов, если они находятся в разделе var
                            self.variables.add(text)
                            self.tokens.append((token_type, text))
                        elif text in self.variables:
                            # Если переменная была объявлена ранее, добавляем её
                            self.tokens.append((token_type, text))
                        else:
                            # Если переменная не была объявлена, выдаём ошибку
                            print(f"Ошибка: Переменная '{text}' использована без объявления.")
                            self.tokens.append(('UNKNOWN', text))
                    elif token_type != 'WHITESPACE':  # Пропускаем пробелы
                        self.tokens.append((token_type, text))
                    self.pos = match.end(0)
                    break
            if not match:
                raise ValueError(f"Нераспознанный символ: {self.code[self.pos]}")
        return self.tokens

# Пример кода для лексического анализа
code1 = """
program var
x, y : integer;
z : real;
v : boolean;
begin
x as 10;
y as 10.2E-5
if x LT y then z as x plus y;
write(x, y, z);
{C}
{
}
{s
c
c
v}
c
v as ~true;
end.
"""

code = """
program
var
x, y : integer;
begin
x as 10;
y as 10.2E-5;
if x LT y then z as x plus y;
write(x, y, z);
end.
"""

# Запуск лексического анализатора
lexer = Lexer(code)
tokens = lexer.tokenize()

# Вывод токенов
for token in tokens:
    print(token)
