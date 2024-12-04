import re

# Определение типов токенов
TOKENS = [
    ('COMMENT', r'\{[^}]*?\}'),  # многострочные комментарии
    ('KEYWORD', r'\b(program|var|begin|end|integer|real|boolean|if|then|else|for|to|do|while|read|write|as)\b'),
    ('OP_REL', r'\b(NE|EQ|LT|LE|GT|GE)\b'),  # операции отношения
    ('BOOLEAN', r'\b(true|false)\b'),  # логические константы
    ('OP_ADD', r'\b(plus|min|or)\b'),  # операции сложения
    ('OP_MUL', r'\b(mult|div|and)\b'),  # операции умножения
    ('OP_UNARY', r'~'),  # унарная операция
    ('ID', r'\b[A-Za-z][A-Za-z0-9]*\b'),  # идентификаторы
    ('BIN', r'\b[01]+[Bb]\b'),  # двоичное число
    ('OCT', r'\b[0-7]+[Oo]\b'),  # восьмеричное число
    ('HEX', r'\b[0-9A-Fa-f]+[Hh]\b'),  # шестнадцатеричное число
    ('REAL', r'\b\d+\.\d+([Ee][+-]?\d+)?\b'),  # действительное число
    ('PUNCT', r'[;:.(),\[\]]'),  # знаки пунктуации
    ('INTEGER', r'\b\d+[Dd]?\b'),  # целое число (десятичное)
    ('WHITESPACE', r'\s+'),  # пробелы и переводы строк
    ('UNKNOWN', r'.'),  # неизвестные символы
]


class Lexer:
    def __init__(self, code):
        self.code = code
        self.pos = 0
        self.tokens = []
        self.variables = set()
        self.in_var_section = False
        self.has_error = False  # Флаг ошибок

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
                            self.has_error = True  # Устанавливаем флаг ошибок
                            self.tokens.append(('UNKNOWN', text))
                    elif token_type != 'WHITESPACE':  # Пропускаем пробелы
                        self.tokens.append((token_type, text))
                    self.pos = match.end(0)
                    break
            if not match:
                raise ValueError(f"Нераспознанный символ: {self.code[self.pos]}")
        return self.tokens

    def get_line_number(self):
        code_lines = self.code.splitlines()
        for i, line in enumerate(code_lines, start=1):
            if any(str(token[1]) in line for token in self.tokens):
                return i
        return None


# Исключение для синтаксических ошибок
class SyntaxError(Exception):
    def __init__(self, message, line_number=0, line_text=0):
        #  super().__init__(f"Syntax error on line {line_number}: {message}\nLine content: {line_text}")
        super().__init__(f"Syntax error: {message}\n")
        self.line_number = line_number
        self.line_text = line_text


# Синтаксический анализатор
class Parser:
    def __init__(self, tokens, code_):
        self.tokens = tokens
        self.code = code_
        self.pos = 0
        self.current_token_index = 0
        self.current_token = self.tokens[self.pos] if self.tokens else None
        self.has_errors = False  # Добавляем флаг наличия ошибок
        self.symbol_table = {}  # Таблица символов для хранения типов переменных
        self.ids = []

    def get_line_number(self):
        code_lines = self.code.splitlines()
        for i, line in enumerate(code_lines, start=1):
            if any(str(token[1]) in line for token in self.tokens):
                return i
        return None

    def get_line_content(self):
        code_lines = self.code.splitlines()
        line_number = self.get_line_number()
        if line_number is not None and 0 <= line_number - 1 < len(code_lines):
            return code_lines[line_number - 1]
        return None

    def get_token(self, number=0):
        if self.current_token_index - number < len(self.tokens):
            return self.tokens[self.current_token_index - number]
        return None

    def next_token(self):
        self.current_token_index += 1
        if self.current_token_index < len(self.tokens):
            self.current_token = self.tokens[self.current_token_index]
            return self.current_token
        return None

    def expect(self, expected_type, expected_value=None, check=False):
        token = self.get_token()
        if check:
            if token and token[0] == expected_type and (expected_value is None or token[1] == expected_value):
                return True
        else:
            if token and token[0] == expected_type and (expected_value is None or token[1] == expected_value):
                self.next_token()
            else:
                line_number = self.get_line_number()
                line_text = self.get_line_content()
                #print(self.get_token())
                #print(self.next_token())
                raise SyntaxError(
                    f"Ожидалось {expected_value if expected_value else expected_type}, было получено {token}",
                    line_number, line_text)

    def parse_program(self):
        try:
            while self.get_token() and self.get_token()[0] == "COMMENT":
                self.next_token()
            # Ожидаем ключевое слово program
            self.expect("KEYWORD", "program")
            while self.get_token() and self.get_token()[0] == "COMMENT":
                self.next_token()

            # Проверка на наличие раздела var
            if self.get_token() and self.get_token()[1] == "var":
                self.expect("KEYWORD", "var")

                # Парсинг идентификаторов в разделе var
                while self.get_token() and self.get_token()[0] == "ID" or self.get_token()[0] == "COMMENT":
                    if self.get_token()[0] == "COMMENT":
                        self.next_token()
                    else:
                        self.parse_declaration()
                    # if self.get_token() and self.get_token()[1] == ";": print(f"if {self.get_token()}")
                    # self.next_token() else: print(f"else {self.get_token()}") print( f"Syntax error on line {
                    # self.get_line_number()}: Expected ';' after declaration, but got {self.get_token()}") print(
                    # f"Line content: {self.get_line_content()}") return
                #  return

            # Начало основной программы
            self.expect("KEYWORD", "begin")

            # Парсинг основной программы
            while self.get_token() and (self.get_token()[0] != "KEYWORD" or self.get_token()[1] != "end"):
                self.parse_statement()

            # Ожидаем end
            self.expect("KEYWORD", "end")
            self.expect("PUNCT", ".")
            while self.get_token() and (self.get_token()[0] != "KEYWORD" or self.get_token()[1] != "end"):
                if self.get_token()[0] == "COMMENT":
                    self.next_token()
                else:
                    self.has_errors = True
                    raise SyntaxError("Обработка команд после end невозможна", 0, 0)
                    break

        except SyntaxError as e:
            self.has_errors = True  # Устанавливаем флаг при ошибке
            print(e)

    # def parse_declaration(self):
    #     self.expect("ID")
    #     while self.get_token() and self.get_token()[1] == ",":
    #         self.next_token()
    #         self.expect("ID")
    #     self.expect("PUNCT", ":")
    #     self.expect("KEYWORD")
    #     self.expect("PUNCT", ";")

    # Метод для парсинга объявлений переменных и их типов
    def parse_declaration(self):
        # ids = []
        ids_n = []
        self.expect("ID", None)
        # print(self.get_token(1)[1])
        if self.get_token(1)[1] not in self.ids:
            self.ids.append(self.get_token(1)[1])
            ids_n.append(self.get_token(1)[1])
        else:
            self.has_errors = True
            raise SyntaxError(f"- повторное описание одного и того же идентификатора ({self.get_token(1)[1]})не "
                              f"разрешается", 0, 0)
        # self.ids.append(self.get_token(1)[1])
        while self.get_token() and self.get_token()[1] == ",":
            self.next_token()
            self.expect("ID", None)
            # print(self.get_token(1)[1])
            if self.get_token(1)[1] not in self.ids:
                self.ids.append(self.get_token(1)[1])
                ids_n.append(self.get_token(1)[1])
            else:
                self.has_errors = True
                raise SyntaxError(f"- повторное описание одного и того же идентификатора ({self.get_token(1)[1]}) не "
                                  f"разрешается", 0, 0)
            # self.ids.append(self.get_token(1)[1])
        self.expect("PUNCT", ":")
        type_token = self.get_token()
        self.expect("KEYWORD", None)

        # Сохраняем тип для каждой переменной в таблице символов
        for var_id in ids_n:
            self.symbol_table[var_id] = type_token[1]

        # print(self.symbol_table)
        self.expect("PUNCT", ";")

    def parse_statement(self, type_statement="None"):
        token = self.get_token()
        #print(token)
        #print(type_statement)

        if type_statement == "compound":
            if token[1] == ":":
                token = self.next_token()
            if token[1] == "if":
                self.parse_if_statement("compound")
            elif token[1] == "while":
                self.parse_while_loop("compound")
            elif token[1] == "for":
                self.parse_for_loop("compound")
            elif token[1] == "read":
                self.parse_read_statement()
            elif token[1] == "write":
                self.parse_write_statement()
            elif token[0] == "ID":
                self.parse_assignment()
            elif token[0] == "COMMENT":
                self.parse_comment()
            elif token[0] == "PUNCT" and token[1] == "[":
                self.parse_compound_statement()
            else:
                # print(self.get_token())
                # print(self.next_token())
                # print(token[0])
                raise SyntaxError(f"Непредвиденное выражение {token[1]}", self.get_line_number(), self.get_line_content())
        else:
            if token[1] == "if":
                self.parse_if_statement()
            elif token[1] == "while":
                self.parse_while_loop()
            elif token[1] == "for":
                self.parse_for_loop()
            elif token[1] == "read":
                self.parse_read_statement()
            elif token[1] == "write":
                self.parse_write_statement()
            elif token[0] == "ID":
                self.parse_assignment()
            elif token[0] == "COMMENT":
                self.parse_comment()
            elif token[0] == "PUNCT" and token[1] == "[":
                self.parse_compound_statement()
            else:
                # print(self.get_token())
                # print(self.next_token())
                # print(token[0])
                raise SyntaxError(f"Непредвиденное выражение {token[1]}", self.get_line_number(), self.get_line_content())

    def parse_compound_statement(self):
        self.expect("PUNCT", "[")
        #print("Still compound statement")
        while self.get_token() and self.get_token()[1] != "]":
            #print(self.get_token())
            if self.get_token()[1] == ":":
                self.expect("PUNCT", ":")
            self.parse_statement("compound")
        #print("Not compound statement")
        self.expect("PUNCT", "]")
        self.expect("PUNCT", ";")

    def parse_if_statement(self, type_of_statement="None"):
        self.expect("KEYWORD", "if")
        #print(type_of_statement+"type")
        self.parse_expression()
        # if type_of_statement == "compound":
        #     self.parse_expression()  # Парсим условие `if`
        # else:
        #     self.parse_expression()
        self.expect("KEYWORD", "then")
        # self.parse_statement()  # Парсим оператор `then`

        # Проверяем, будет ли составной оператор
        if self.get_token() and self.get_token()[1] == "[":
            self.parse_compound_statement()
        else:
            if type_of_statement == "compound":
                self.parse_statement("compound")
            else:
                self.parse_statement()

        # Проверка наличия блока `else`
        if self.get_token() and self.get_token()[1] == "else":
            self.expect("KEYWORD", "else")
            if type_of_statement == "compound":
                self.parse_statement("compound")  # Парсим оператор `else`
            else:
                self.parse_statement()

    def parse_comment(self):
        self.expect("COMMENT")

    def parse_write_statement(self):
        self.expect("KEYWORD", "write")
        self.expect("PUNCT", "(")
        self.parse_expression()  # Парсим первое выражение для вывода

        # Парсим дополнительные выражения, если они есть
        while self.get_token() and self.get_token()[1] == ",":
            self.next_token()  # Пропускаем запятую
            self.parse_expression()  # Парсим следующее выражение
        self.expect("PUNCT", ")")
        self.expect("PUNCT", ";")

    def parse_expression(self, info="None"):
        if info == "None":
            # Парсим операнды и операторы
            self.expect("ID", None)
            while self.get_token() and self.get_token()[0] in ["OP_REL", "OP_ADD", "OP_MUL"]:
                self.next_token()  # Пропускаем операцию
                if self.expect("ID", None, True):
                    self.expect("ID", None)
                elif self.expect("INTEGER", None, True):
                    self.expect("INTEGER", None)
                elif self.expect("REAL", None, True):
                    self.expect("REAL", None)
                # self.expect("ID", None)
        else:
            self.expect("INTEGER", None)

    # def parse_expression(self):
    #     # Проверка на допустимый токен: ID, INTEGER, REAL или BOOLEAN
    #     if self.get_token() and self.get_token()[0] in ["ID", "INTEGER", "REAL", "BOOLEAN"]:
    #         self.next_token()  # Пропускаем текущий токен
    #     else:
    #         line_number = self.get_line_number()
    #         line_text = self.get_line_content()
    #         expected = "ID, INTEGER, REAL или BOOLEAN"
    #         actual = self.get_token()[1] if self.get_token() else "None"
    #         raise SyntaxError(f"Ожидалось {expected}, было получено {actual}.", line_number, line_text)
    #
    #     # Обработка операторов и дополнительных выражений
    #     while self.get_token() and self.get_token()[0] in ["OP_REL", "OP_ADD", "OP_MUL"]:
    #         self.next_token()  # Пропускаем оператор
    #         if self.get_token() and self.get_token()[0] in ["ID", "INTEGER", "REAL", "BOOLEAN"]:
    #             self.next_token()
    #         else:
    #             line_number = self.get_line_number()
    #             line_text = self.get_line_content()
    #             raise SyntaxError(
    #                 f"Ожидалось ID, INTEGER, REAL или BOOLEAN после оператора.",
    #                 line_number,
    #                 line_text,
    #             )

    def parse_read_statement(self):
        self.expect("KEYWORD", "read")
        self.expect("PUNCT", "(")
        self.expect("ID", None)
        while self.get_token() and self.get_token()[1] == ",":
            self.next_token()
            self.expect("ID", None)
        self.expect("PUNCT", ")")
        self.expect("PUNCT", ";")

    def parse_for_loop(self, type_of_statement="None"):
        self.expect("KEYWORD", "for")
        self.parse_assignment("for")  # Присваивание начального значения
        self.expect("KEYWORD", "to")
        self.parse_expression("for")  # Парсим выражение конца диапазона
        self.expect("KEYWORD", "do")
        # self.parse_statement()  # Парсим оператор цикла
        # Проверяем, будет ли составной оператор
        if self.get_token() and self.get_token()[1] == "[":
            self.parse_compound_statement()
        else:
            if type_of_statement == "compound":
                self.parse_statement("compound")
            else:
                self.parse_statement()

    def parse_while_loop(self, type_of_statement="None"):
        self.expect("KEYWORD", "while")
        self.parse_expression()
        # if type_of_statement == "compound":
        #     self.parse_expression("compound")  # Парсим выражение условия
        # else:
        #     self.parse_expression()
        self.expect("KEYWORD", "do")
        # self.parse_statement()  # Парсим оператор цикла
        # Проверяем, будет ли составной оператор
        if self.get_token() and self.get_token()[1] == "[":
            self.parse_compound_statement()
        else:
            if type_of_statement == "compound":
                self.parse_statement("compound")
            else:
                self.parse_statement()

    def parse_assignment(self, info="None"):
        var_name = self.get_token()[1]
        var_type = self.symbol_table.get(var_name)

        self.expect("ID", None)
        self.expect("KEYWORD", "as")

        # Проверка типа данных
        if var_type == "integer":
            #print(var_name)
            #print(var_type)
            #print(self.get_token())
            if self.get_token()[0] == "INTEGER":
                self.next_token()
            elif self.get_token()[0] == "REAL" or self.get_token()[0] == "BOOLEAN":
                raise SyntaxError(f"Неподходящий тип данных для переменной  '{var_name}'", self.get_line_number(),
                                  self.get_line_content())
            else:
                self.parse_expression()
        elif var_type == "real":
            if self.get_token()[0] == "REAL" or self.get_token()[0] == "INTEGER":
                self.next_token()
            elif self.get_token()[0] == "BOOLEAN":
                raise SyntaxError(f"Неподходящий тип данных для переменной  '{var_name}'", self.get_line_number(),
                                  self.get_line_content())
            else:
                self.parse_expression()
        elif var_type == "boolean":
            if self.get_token()[0] == "BOOLEAN":
                self.next_token()
            elif self.get_token()[0] == "REAL" or self.get_token()[0] == "INTEGER":
                raise SyntaxError(f"Неподходящий тип данных для переменной '{var_name}'", self.get_line_number(),
                                  self.get_line_content())
            else:
                self.parse_expression()
        else:
            raise SyntaxError(f"Неизвестный тип данных для переменной '{var_name}'", self.get_line_number(),
                              self.get_line_content())

        if info == "None":
            # Завершаем инструкцию присваивания
            self.expect("PUNCT", ";")
        else:
            pass

    # def parse_statement(self):
    #     if self.get_token()[1] == "if":
    #         print("if")
    #         self.expect("KEYWORD", "if")
    #         self.expect("ID")
    #         self.expect("OP_REL")
    #         self.expect("ID")
    #         print("if")
    #         self.expect("KEYWORD", "then")
    #         self.parse_statement()
    #     elif self.get_token()[1] == "write":
    #         self.expect("KEYWORD", "write")
    #         self.expect("PUNCT", "(")
    #         self.expect("ID")
    # while self.get_token() and self.get_token()[1] == ",":
    #     self.next_token()
    #     self.expect("ID")
    # self.expect("PUNCT", ")")


# Лексический анализ и синтаксический разбор
code1 = """
program
var
x, y : integer;
begin
x as 10;
y as 10.2E-5;
if x LT y  z as x plus y;
write(x, y, z);
end.
"""

code = """
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
v as ~true;
end.
"""
code2 = """
program var
x, y : integer;
z : real;
v : boolean;
begin
x as 10;
y as 20;
for x as 1 to 10 do
    write(x);
while y LT z do
    y as y plus 1;
if x LT y then
    z as x plus y;
else
    z as x min y;
write(x, y, z);
read(x, y);
end.
"""

code3 = """ {dfadfaf} program {dfadfaf}
var
{dfadfaf}
x,y : integer;
w : boolean;
{dfadfaf}
z : real;
begin
x as 10;
{dfadfaf}
y as 22; 
{dfadfaf}
z as 10.3222E+0;
w as true;
if x GT y then
write(x);
else
read(z);
end.
for
{dfadfaf}
begin
"""
code4 = """
program var
x, y : integer;
z : real;
v : boolean;
begin
[
x as 10;
y as 20;
for x as 1 to 10 do
[
: write(x);
    ];
while y LT z do
    y as y plus 1;
if x LT y then
   : z as x plus y;
else
    z as x min y;
    ];
write(x, y, z);
read(x, y);
end.
"""

# lexer = Lexer(code1)  # создаем лексер с исходным кодом
# tokens = lexer.tokenize()  # получаем токены
# print(tokens)
# parser = Parser(tokens, code)  # передаем токены и исходный код в парсер
# parser.parse_program()  # запускаем синтаксический анализ
#
# # Проверяем наличие ошибок
# if not parser.has_errors and not lexer.has_error:
#     print("Все верно")

def process_code(code, name="default"):
    print(f"Результат для {name}: ")
    lexer = Lexer(code)  # создаем лексер с исходным кодом
    tokens = lexer.tokenize()  # получаем токены
    # print(tokens)
    parser = Parser(tokens, code)  # передаем токены и исходный код в парсер
    parser.parse_program()  # запускаем синтаксический анализ
    # Проверяем наличие ошибок
    if not parser.has_errors and not lexer.has_error:
        print("Все верно")


# Обработка каждого кода
process_code(code, "program 0")
process_code(code1, "program 1")
process_code(code2, "program 2")
process_code(code3, "program 3")
process_code(code4, "program 4")
