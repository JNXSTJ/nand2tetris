# coding=utf-8
import os.path
import os

C_ARITHMATIC = "C_ARITHMATIC"
C_PUSH = "C_PUSH"
C_POP = "C_POP"
C_COMMENT = "C_COMMENT"
C_EMPTY_LINE = "C_EMPTY_LINE"

ADD = "add"
SUB = "sub"
NEG = "neg"
EQ = "eq"
GT = "gt"
LT = "lt"
AND = "and"
OR = "or"
NOT = "not"

operands = {
    ADD: "add",
    SUB: "sub",
    NEG: "neg",
    EQ: "eq",
    GT: "gt",
    LT: "lt",
    AND: "and",
    OR: "or",
    NOT: "not",
}

LOCAL = 'local'
ARGUMENT = 'argument'
STATIC = 'static'
CONSTANT = 'constant'
THIS = 'this'
THAT = 'that'
TEMP = 'temp'
POINTER = 'pointer'

segments = {
    LOCAL: 'local',
    ARGUMENT: 'argument',
    STATIC: 'static',
    CONSTANT: 'constant',
    THIS: 'this',
    THAT: 'that',
    TEMP: 'temp',
    POINTER: 'pointer',
}

TEMP_SEGMENT_BASE_ADDRESS = 5 # 5 ~ 12
STATIC_SEGMENT_BASE_ADDRESS = 16 # 16 ~ 255
# 下面这些数字分别存放了指向了各个段起始地址的指针
#SP = 0
#LCL = 1
#ARG = 2
#THIS = 3
#THAT = 4

g_label_idx = 0
def get_label():
    global g_label_idx
    g_label_idx += 1
    return f'label_{g_label_idx}'


class Command(object):
    def __init__(self, line: str):
        self._command_type = ""
        self._arg1: str = ""
        self._arg2: int = -1
        self._line = line
        self.init(line)

    def init(self, line):
        line = line.strip(' \n')
        print(line)
        if len(line) == 0:
            self._command_type = C_EMPTY_LINE
            return
        if line.startswith('//'):
            self._command_type = C_COMMENT
            return
        elif line.startswith('push'):
            self._command_type = C_PUSH
            self._arg1 = line.split(' ')[1]
            self._arg2 = int(line.split(' ')[2])
            assert self._arg1 in segments
        elif line.startswith('pop'):
            self._command_type = C_POP
            self._arg1 = line.split(' ')[1]
            self._arg2 = int(line.split(' ')[2])
            assert self._arg1 in segments
        elif line in operands:
            self._command_type = C_ARITHMATIC
            self._arg1 = line
        else:
            assert False, "never reach here"

    def command_type(self):
        return self._command_type

    def arg1(self) -> str:
        return self._arg1

    def arg2(self) -> int:
        return self._arg2


class Parser(object):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.commands = []
        self.idx = -1
        self.init()

    def init(self):
        with open(self.path, 'r') as f:
            for line in f.readlines():
                command = Command(line)
                self.commands.append(command)

    def has_more_lines(self) -> bool:
        return self.idx + 1 < len(self.commands) and len(self.commands) > 0

    def advance(self):
        self.idx += 1

    def command(self):
        return self.commands[self.idx]


class CodeWriter(object):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.lines = []
        self.base_name = os.path.basename(self.path).split('.')[0]

    def write_arithmatic(self, command: Command):
        def add_func(command: Command) -> [str]:
            return [
                # sp--
                # d = RAM[sp]
                # sp--
                # RAM[sp] += d
                # sp++

                # sp--
                '@SP',
                'M=M-1',
                # d = RAM[sp]
                '@SP',
                'A=M',
                'D=M',
                # sp--
                '@SP',
                'M=M-1',
                # RAM[sp] += d
                '@SP',
                'A=M',
                'M=D+M',
                # sp++
                '@SP',
                'M=M+1'
            ]

        def sub_func(command: Command) -> [str]:
            return [
                # sp--
                # d = RAM[sp]
                # sp--
                # RAM[sp] -= d
                # sp++

                # sp--
                '@SP',
                'M=M-1',
                # d = RAM[sp]
                '@SP',
                'A=M',
                'D=M',
                # sp--
                '@SP',
                'M=M-1',
                # RAM[sp] += d
                '@SP',
                'A=M',
                'M=M-D',
                # sp++
                '@SP',
                'M=M+1'
            ]

        def neg_func(command: Command) -> [str]:
            return [
                # RAM[sp - 1] = -RAM[sp - 1]
                'D=0',
                '@SP',
                'A=M',
                'A=A-1',
                'M=D-M'
            ]

        def eq_func(command: Command) -> [str]:
            final_label = get_label()
            eq_label = get_label()
            return [
                # RAM[sp - 1] = RAM[sp - 1] == RAM[sp - 2]
                # sp = sp - 1
                '@SP',
                'M=M-1',
                'A=M',
                'D=M',

                '@SP',
                'M=M-1',
                'A=M',
                'D=D-M',

                f'@{eq_label}',
                f'D;JEQ',

                # not equal
                'D=0',

                f'@{final_label}',
                '0;JMP',

                f'({eq_label})',
                'D=-1',

                f'({final_label})',
                # RAM[sp] = D
                '@SP',
                'A=M',
                'M=D',

                # SP++
                '@SP',
                'M=M+1'
            ]

        def gt_func(command: Command) -> [str]:
            final_label = get_label()
            gt_label = get_label()
            return [
                # RAM[sp - 1] = RAM[sp - 1] == RAM[sp - 2]
                # sp = sp - 1
                '@SP',
                'M=M-1',
                'A=M',
                'D=M',

                '@SP',
                'M=M-1',
                'A=M',
                'D=M-D',

                f'@{gt_label}',
                f'D;JGT',
                # not equal
                'D=0',

                f'@{final_label}',
                '0;JMP',

                f'({gt_label})',
                'D=-1',

                f'({final_label})',
                # RAM[sp] = D
                '@SP',
                'A=M',
                'M=D',

                # SP++
                '@SP',
                'M=M+1'
            ]

        def lt_func(command: Command) -> [str]:
            final_label = get_label()
            lt_label = get_label()
            return [
                # RAM[sp - 1] = RAM[sp - 1] == RAM[sp - 2]
                # sp = sp - 1
                '@SP',
                'M=M-1',
                'A=M',
                'D=M',

                '@SP',
                'M=M-1',
                'A=M',
                'D=M-D',

                f'@{lt_label}',
                f'D;JLT',
                # not equal
                'D=0',

                f'@{final_label}',
                '0;JMP',

                f'({lt_label})',
                'D=-1',

                f'({final_label})',
                # RAM[sp] = D
                '@SP',
                'A=M',
                'M=D',

                # SP++
                '@SP',
                'M=M+1'
            ]

        def and_func(command: Command) -> [str]:
            return [
                # sp--
                # d = RAM[sp]
                # sp--
                # RAM[sp] = RAM[sp] & d
                # sp++

                # sp--
                '@SP',
                'M=M-1',
                # d = RAM[sp]
                '@SP',
                'A=M',
                'D=M',
                # sp--
                '@SP',
                'M=M-1',
                # RAM[sp] += d
                '@SP',
                'A=M',
                'M=D&M',
                # sp++
                '@SP',
                'M=M+1'
            ]

        def or_func(command: Command) -> [str]:
            return [
                # sp--
                # d = RAM[sp]
                # sp--
                # RAM[sp] = RAM[sp] | d
                # sp++

                # sp--
                '@SP',
                'M=M-1',
                # d = RAM[sp]
                '@SP',
                'A=M',
                'D=M',
                # sp--
                '@SP',
                'M=M-1',
                # RAM[sp] += d
                '@SP',
                'A=M',
                'M=D|M',
                # sp++
                '@SP',
                'M=M+1'
            ]

        def not_func(command: Command) -> [str]:
            return [
                # RAM[sp - 1] = !RAM[sp - 1]
                '@SP',
                'A=M',
                'A=A-1',
                'M=!M'
            ]

        operands = {
            ADD: add_func,
            SUB: sub_func,
            NEG: neg_func,
            EQ: eq_func,
            GT: gt_func,
            LT: lt_func,
            AND: and_func,
            OR: or_func,
            NOT: not_func,
        }
        assert command.command_type() == C_ARITHMATIC
        func = operands[command.arg1()]
        self.lines.extend(func(command))

    def write_push(self, command: Command) -> [str]:
        def push_constant(command: Command) -> [str]:
            return [
                # D=i
                f'@{command.arg2()}',
                'D=A',
                # RAM[sp] = constant
                '@SP',
                'A=M',
                'M=D',
                # sp++
                '@SP',
                'M=M+1'
            ]

        def push_local_argument_this_that(command: Command) -> [str]:
            segments = {
                'local': 'LCL',
                'argument': 'ARG',
                'this': 'THIS',
                'that': 'THAT'
            }
            return [
                # addr = seg + i
                # RAM[sp] = RAM[addr]
                # sp--
                f'@{segments[command.arg1()]}',
                'D=M',
                f'@{command.arg2()}',
                'A=D+A',
                'D=M',
                '@SP',
                'A=M',
                'M=D',

                '@SP',
                'M=M+1',
            ]

        def push_static(command: Command) -> [str]:
            return [
                # RAM[SP] = StaticTest.2
                # f'push {self.base_name}.{command.arg2()}',
                f'@{self.base_name}.{command.arg2()}',
                'D=M',
                '@SP',
                'A=M',
                'M=D',
                '@SP',
                'M=M+1'
            ]

        def push_temp(command: Command) -> [str]:
            return [
                f'push RAM[5+{command.arg2()}]'
            ]

        def push_pointer(command: Command) -> [str]:
            if command.arg2() == 0:
                # this
                address = 3
            elif command.arg2() == 1:
                # that
                address = 4
            else:
                assert False
            return [
                f'@{address}',
                'D=M',
                '@SP',
                'A=M',
                'M=D',
                '@SP',
                'M=M+1',
            ]

        segments = {
            LOCAL: push_local_argument_this_that,
            ARGUMENT: push_local_argument_this_that,
            STATIC: push_static,
            CONSTANT: push_constant,
            THIS: push_local_argument_this_that,
            THAT: push_local_argument_this_that,
            TEMP: push_temp,
            POINTER: push_pointer
        }
        segment_func = segments.get(command.arg1())
        self.lines.extend(segment_func(command))

    def write_pop(self, command: Command) -> [str]:
        def pop_constant(command: Command) -> [str]:
            assert False

        def pop_local_argument_this_that(command: Command) -> [str]:
            segments = {
                'local': 'LCL',
                'argument': 'ARG',
                'this': 'THIS',
                'that': 'THAT'
            }
            return [
                # addr = LCL + i
                # sp--
                # RAM[addr] = RAM[sp]
                '@SP',
                'M=M-1',
                'A=M',
                'D=M',
                '@R13',
                'M=D',

                f'@{segments[command.arg1()]}',
                'D=M',
                f'@{command.arg2()}',
                'D=D+A',
                '@R14',
                'M=D',

                '@R13',
                'D=M',

                '@R14',
                'A=M',
                'M=D'
            ]

        def pop_static(command: Command) -> [str]:
            return [
                # StaticTest.2 = RAM[sp - 1]
                # f'pop {self.base_name}.{command.arg2()}'
                '@SP',
                'M=M-1',
                'A=M',
                'D=M',
                f'@{self.base_name}.{command.arg2()}',
                'M=D'
            ]

        def pop_temp(command: Command) -> [str]:
            return [
                f'pop RAM[5+{command.arg2()}]'
            ]

        def pop_pointer(command: Command) -> [str]:
            if command.arg2() == 0:
                # this
                address = 3
            elif command.arg2() == 1:
                # that
                address = 4
            else:
                assert False
            return [
                '@SP',
                'M=M-1',
                'A=M',
                'D=M',
                f'@{address}',
                'M=D'
            ]

        segments = {
            LOCAL: pop_local_argument_this_that,
            ARGUMENT: pop_local_argument_this_that,
            STATIC: pop_static,
            CONSTANT: pop_constant,
            THIS: pop_local_argument_this_that,
            THAT: pop_local_argument_this_that,
            TEMP: pop_temp,
            POINTER: pop_pointer
        }
        segment_func = segments.get(command.arg1())
        self.lines.extend(segment_func(command))
        pass

    def close(self):
        output_file = self.path.replace(".vm", ".asm")
        with open(output_file, 'w') as f:
            f.write('\n'.join(self.lines))


class VMTranslator(object):
    def __init__(self, path):
        super().__init__()
        self.parser = Parser(path)
        self.codeWriter = CodeWriter(path)

    def parse(self):
        while self.parser.has_more_lines():
            self.parser.advance()
            command = self.parser.command()
            if command.command_type() == C_COMMENT or command.command_type() == C_EMPTY_LINE:
                continue
            if False:
                self.codeWriter.lines.append(command._line)
            if command.command_type() == C_ARITHMATIC:
                self.codeWriter.write_arithmatic(command)
            elif command.command_type() == C_PUSH:
                self.codeWriter.write_push(command)
            elif command.command_type() == C_POP:
                self.codeWriter.write_pop(command)
            else:
                assert False, "unknown command type"
        self.codeWriter.close()


def main():
    import os
    dirname = os.path.dirname(__file__)
    dirname = os.path.dirname(dirname)
    path = os.path.join(dirname, R'projects\07\PointerTest\PointerTest.vm')
    vmTranslator = VMTranslator(path)
    vmTranslator.parse()


if __name__ == "__main__":
    main()
