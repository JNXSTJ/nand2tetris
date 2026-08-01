// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Fill.asm

// Runs an infinite loop that listens to the keyboard input. 
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, 
// the screen should be cleared.

//// Replace this comment with your code.
// m0 0 or -1  m1 pointer
(LOOP)
// set pointer
@SCREEN
D=A
@8192
D=D+A
@1
M=D
@KBD
D=M
@WHITE
D;JEQ
(BLACK)
@0
M=-1
@ALL
0;JMP
(WHITE)
@0
M=0
(ALL)
// 从m1取出指针，并减掉1，再存到m1
@1
M=M-1
// 赋值
@0
D=M
@1
A=M
M=D
// 如果等于0，跳转到loop
@1
D=M
@SCREEN
D=D-A
@LOOP
D;JEQ
@ALL
0;JMP