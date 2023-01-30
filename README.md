# Shirasu

## Introduction

`Shirasu` is a simple bot framework to study the principles, based on  `OneBot v11` (especially `go-cqhttp`).

出于练习英语的目的，本篇我就用简单英文写了（来自寒假末尾最后的倔强，其实是 Grammarly 监督才能避免一堆语法错误）。


## Features

+ Dependency Injection System, based on certain names with type-checking at runtime.

  I'm used to Spring's dependency injection system, which is like:

  ```java
  @Autowired
  private Foo foo;
  ```

  I know it's better to use a setter or constructor, but let me just keep it simple.

  However, dependency injection in `FastAPI` is like this:

  ```python
  async def get_foo() -> Foo:
      return Foo()
  
  async def use(foo: Foo = Depends(get_foo)) -> None:
      await foo.use()
  ```

  There are other frameworks like what Spring does for sure, but to study the principles, I implemented a simple dependency injection system.

  ```python
  from shirasu.di import inject, provide
  from datetime import datetime
  
  @provide('now')
  async def provide_now() -> datetime:
      return datetime.now()
  
  @inject()
  async def use_now(now: datetime) -> None:
      print(now.strftime('%Y-%m-%d %H:%M:%S'))
  
  @inject()
  async def use_now_wrong_type(now: int) -> None:
      print(f'This will not be executed because {now} is a datetime, not an int.')
  
  # Prints current datetime.
  await use_now()
  
  # Raises.
  await use_now_wrong_type()
  ```

  To keep the code simple, everything should be `async`.

  The annotation of each injected parameter **cannot be a string**(e.g. using `"datetime"` as the annotation for the parameter `now` is incorrect).

  They should be real types because the injector will check if they are correct.

+ Addon System, without the need of ensuring import orders.

  Write later.

+ Convenient(Maybe) Configuration.

  Write later.


+ Easy to test.

  Writer later.

