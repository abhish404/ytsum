### 1: Intro [0:00](https://www.youtube.com/watch?v=63zGtiv89bA&t=0s)

[0:00](https://www.youtube.com/watch?v=63zGtiv89bA&t=0s) C was one of the first high-level languages to gain widespread adoption. It's since become the foundation for modern operating systems, databases, and other languages. Yet, because of its
[0:10](https://www.youtube.com/watch?v=63zGtiv89bA&t=10s) age, it has a lot of surprising behaviors, many of which have been propagated to other programming languages. One of these is sometimes given as an example of why JavaScript is
[0:19](https://www.youtube.com/watch?v=63zGtiv89bA&t=19s) weird, even though the main source of confusion has its origins in C. Today, I've compiled a list of my favorite facts about C. We'll start with
[0:27](https://www.youtube.com/watch?v=63zGtiv89bA&t=27s) the things you really ought to know and then we'll get further down into the more obscure. For those unfamiliar,

### 2: Pointers [0:31](https://www.youtube.com/watch?v=63zGtiv89bA&t=31s)

[0:32](https://www.youtube.com/watch?v=63zGtiv89bA&t=32s) let's quickly review one of C's most essential concepts, pointers. At their core, pointers are just variables that point to the location of another variable in memory. The syntax can be a
[0:42](https://www.youtube.com/watch?v=63zGtiv89bA&t=42s) little confusing at first. If you write int star p, you're declaring an integer pointer called p. amperand a gives you the memory address of variable a. Then
[0:53](https://www.youtube.com/watch?v=63zGtiv89bA&t=53s) star p gives you the value that p points to. One of the first times pointers

### 3: Arrays are (not) pointers [0:56](https://www.youtube.com/watch?v=63zGtiv89bA&t=56s)

[0:58](https://www.youtube.com/watch?v=63zGtiv89bA&t=58s) really clicked for me was when I learned that arrays are but not exactly pointers. An array is essentially just a pointer to the first
[1:06](https://www.youtube.com/watch?v=63zGtiv89bA&t=66s) element in that array. This is where pointer arithmetic comes in. If you add one to your pointer, C gives you the address of the second element in that array, accounting for the size of each
[1:16](https://www.youtube.com/watch?v=63zGtiv89bA&t=76s) element automatically. In this way, dreferencing array + one is equivalent to indexing your array at index 1. And the same is true in general.
[1:24](https://www.youtube.com/watch?v=63zGtiv89bA&t=84s) Dreferencing array plus index is equivalent to getting the value of your array at that index. Now, here's where it gets interesting. If array at index
[1:32](https://www.youtube.com/watch?v=63zGtiv89bA&t=92s) is equivalent to dreferencing array plus index, and addition is commutative, then this must be equivalent to swapping index and the array. And indeed, it is.
[1:42](https://www.youtube.com/watch?v=63zGtiv89bA&t=102s) You can write index array of two in C and it will compile and work exactly the same as getting index 2 of array. It's a fun party trick. arrays
[1:51](https://www.youtube.com/watch?v=63zGtiv89bA&t=111s) act pointers, but that doesn't mean that arrays are pointers. What we're observing here is called array decay. The automatic conversion of arrays to pointers in certain contexts. Switching

### 4: The stack [2:00](https://www.youtube.com/watch?v=63zGtiv89bA&t=120s)

[2:01](https://www.youtube.com/watch?v=63zGtiv89bA&t=121s) gears, what happens when you call a function? , your program maintains something called the stack. When you call a function, a new stack
[2:09](https://www.youtube.com/watch?v=63zGtiv89bA&t=129s) frame gets pushed onto the stack. This frame contains all the local variables for that function as as information about where to return to when the function finishes. When the function
[2:18](https://www.youtube.com/watch?v=63zGtiv89bA&t=138s) returns, the stack frame gets popped off and all those local variables are gone. This leads to a common mistake, returning a pointer to a stack variable. Let's say you have a function that
[2:27](https://www.youtube.com/watch?v=63zGtiv89bA&t=147s) creates an integer, stores it in a local variable, and then returns a pointer to that variable. Once the function returns, that memory is no longer valid.
[2:35](https://www.youtube.com/watch?v=63zGtiv89bA&t=155s) Your pointer could now be pointing to garbage, and using it counts as undefined behavior. The alternative to

### 5: The heap [2:40](https://www.youtube.com/watch?v=63zGtiv89bA&t=160s)

[2:41](https://www.youtube.com/watch?v=63zGtiv89bA&t=161s) the stack is the heap. If you need memory that outlives a function call or if you need a lot of memory, you'll probably be using the heap. The heap is a region of memory that you can allocate
[2:50](https://www.youtube.com/watch?v=63zGtiv89bA&t=170s) and free manually. To allocate memory on the heap, you just use malo, which stands for memory allocate, and you tell it how many bytes you need, and it gives you a pointer to that memory. When
[3:00](https://www.youtube.com/watch?v=63zGtiv89bA&t=180s) you're done with it, you can call free to give it back. If you forget to free memory that you've allocated, you have what's called a memory leak. your program will keep using more and more
[3:08](https://www.youtube.com/watch?v=63zGtiv89bA&t=188s) memory until it eventually slows down or cracks.

### 6: Struct alignment [3:12](https://www.youtube.com/watch?v=63zGtiv89bA&t=192s)

[3:12](https://www.youtube.com/watch?v=63zGtiv89bA&t=192s) Next, let's talk about strrus. A strruct is just a way to group related variables together. It's a class in an object-oriented language. Now, here's
[3:20](https://www.youtube.com/watch?v=63zGtiv89bA&t=200s) a question. How much memory does this strct take up? You might think that a car is one byte and an int is four bytes. , that's 1 + 4 + 1 is 6 bytes
[3:29](https://www.youtube.com/watch?v=63zGtiv89bA&t=209s) total, right? , not quite. On most systems, this strct will take up 12 bytes. Why? Because of something called strruct alignment, modern
[3:38](https://www.youtube.com/watch?v=63zGtiv89bA&t=218s) processors are optimized to read memory in chunks, usually four or eight bytes at a time. To make this efficient, the compiler adds padding to align fields to
[3:47](https://www.youtube.com/watch?v=63zGtiv89bA&t=227s) addresses that are multiples of their size. After that first character, the compiler adds three bytes of padding that the int starts on a four byte boundary. Then after the second car, it
[3:57](https://www.youtube.com/watch?v=63zGtiv89bA&t=237s) adds three more bytes. the entire struck size is a multiple of four. But if we rearrange the fields this, now it only takes eight bytes. The two
[4:05](https://www.youtube.com/watch?v=63zGtiv89bA&t=245s) car fields can sit next to each other without wasting space. The takeaway is that the field order matters when you're defining strcts. Grouping smaller types together can save significant memory,
[4:14](https://www.youtube.com/watch?v=63zGtiv89bA&t=254s) especially if you're creating millions of them or are programming for a system with heavy memory limitations. Next,

### 7: Crazy compiler optimizations [4:19](https://www.youtube.com/watch?v=63zGtiv89bA&t=259s)

[4:20](https://www.youtube.com/watch?v=63zGtiv89bA&t=260s) let's talk about the compiler a bit. In particular, its gnarly optimizations. A really cool example is something called scalar evolution. Let's say you write a
[4:29](https://www.youtube.com/watch?v=63zGtiv89bA&t=269s) simple loop to calculate the sum of integers from 1 to n. This code has O of N time complexity. If you double n, it should take twice as long to run. But if
[4:37](https://www.youtube.com/watch?v=63zGtiv89bA&t=277s) you compile this with even basic optimizations, the compiler knows that it can replace the entire loop with the formula for triangular numbers. Your code is now O of one. And apparently
[4:47](https://www.youtube.com/watch?v=63zGtiv89bA&t=287s) it's not doing this by pattern matching. It is figuring it out from first principles. Now, this is a pretty extreme example of a compiler optimization, but in general, the rule
[4:56](https://www.youtube.com/watch?v=63zGtiv89bA&t=296s) of thumb is that you should focus on writing good algorithms in readable ways. Minor changes in the name of optimization that obfuscate your code are often not necessary and can even
[5:05](https://www.youtube.com/watch?v=63zGtiv89bA&t=305s) hurt performance if you're not careful. Now we're getting a bit deeper in the iceberg towards things that might surprise you even if you have a bit of experience in C. By the way, if you're
[5:14](https://www.youtube.com/watch?v=63zGtiv89bA&t=314s) enjoying the video, please let me know by liking it or subscribing. It really helps me out. C lets you operate on the

### 8: Bitwise operations on signed types [5:19](https://www.youtube.com/watch?v=63zGtiv89bA&t=319s)

[5:20](https://www.youtube.com/watch?v=63zGtiv89bA&t=320s) individual bits of data with bitwise operations. What happens if you do this with a negative number? To answer that, we first need to talk about how negative numbers are stored. On virtually all
[5:29](https://www.youtube.com/watch?v=63zGtiv89bA&t=329s) modern systems, negative integers are represented using two's complement. Two's complement works a lot binary, except instead of the most significant bit being a power of two,
[5:38](https://www.youtube.com/watch?v=63zGtiv89bA&t=338s) it's the negative of its typical value. Before 2023, the C standard never required two's complement representation for signed integers. , Bitwise
[5:47](https://www.youtube.com/watch?v=63zGtiv89bA&t=347s) operations on signed integers were implementation specific. As of C23, two's complement is now required. And these operations are finally 

### 9: Unsafe behaviour in the C standard library [5:56](https://www.youtube.com/watch?v=63zGtiv89bA&t=356s)

[5:56](https://www.youtube.com/watch?v=63zGtiv89bA&t=356s) defined. Something you should definitely know. The C standard library contains unsafe functions. Take stir copy for example. It copies a string from one location to another, but it doesn't
[6:05](https://www.youtube.com/watch?v=63zGtiv89bA&t=365s) check if the destination buffer is large enough. If the source string is longer than the destination buffer, you have a buffer overflow, which can be a big problem. Another one is A2I, which
[6:15](https://www.youtube.com/watch?v=63zGtiv89bA&t=375s) converts a string to an integer. The problem is it has no way to report errors. It will try to parse the string you give it and will fail silently.

### 10: Digraphs and trigraphs [6:23](https://www.youtube.com/watch?v=63zGtiv89bA&t=383s)

[6:23](https://www.youtube.com/watch?v=63zGtiv89bA&t=383s) Now, here's something that exists purely because C is old, but is totally useless today. Back in the day, not all keyboards had characters the curly
[6:31](https://www.youtube.com/watch?v=63zGtiv89bA&t=391s) brackets. , the C standard introduced diagraphs and trigraphs as alternative ways to write these characters. Diagraphs are two character sequences
[6:39](https://www.youtube.com/watch?v=63zGtiv89bA&t=399s) that represent single characters. For example, less than percent and percent greater than can be used instead of the curly brackets. This means that this
[6:48](https://www.youtube.com/watch?v=63zGtiv89bA&t=408s) code is completely valid C. We can make it even uglier with triraphphs which use three character sequences starting with two question marks. These days
[6:56](https://www.youtube.com/watch?v=63zGtiv89bA&t=416s) triigraphs will give you a compiler warning by default and need to be enabled with a compiler flag. Now

### 11: main is not _start [7:01](https://www.youtube.com/watch?v=63zGtiv89bA&t=421s)

[7:01](https://www.youtube.com/watch?v=63zGtiv89bA&t=421s) something that's fun to know but a little more useful is that main is not the true entry point of your program. Before main runs, the program has to do a bunch of setup work. It needs to
[7:10](https://www.youtube.com/watch?v=63zGtiv89bA&t=430s) prepare the command line arguments, initialize the C standard library, and on. This all happens in a function called underscore start. You can customize your start function, giving
[7:19](https://www.youtube.com/watch?v=63zGtiv89bA&t=439s) you complete control over the program's initialization. Sometimes this is necessary if you want to be free from lib C. For example, if you're writing a very minimal program or working in an
[7:28](https://www.youtube.com/watch?v=63zGtiv89bA&t=448s) embedded environment, you might want to skip all of the standard library setup and do it yourself. Now, this fact is

### 12: A byte is not 8 bits [7:33](https://www.youtube.com/watch?v=63zGtiv89bA&t=453s)

[7:34](https://www.youtube.com/watch?v=63zGtiv89bA&t=454s) one of my favorites because it sounds pedantic, but can be important to know. One of the most common data types in C is the character car. You may
[7:43](https://www.youtube.com/watch?v=63zGtiv89bA&t=463s) know that a car is one bite and you probably also know that one bite is eight bits. But , while the C standard does guarantee that a car is
[7:52](https://www.youtube.com/watch?v=63zGtiv89bA&t=472s) one bite, it says nothing about how many bits are in a bite. And because it's never directly defined, it's technically implementation specific. There are
[8:01](https://www.youtube.com/watch?v=63zGtiv89bA&t=481s) architectures where the number of bits in a bite can be 16, 32, or even 24. You usually see this in digital signal processors or embedded systems where the
[8:11](https://www.youtube.com/watch?v=63zGtiv89bA&t=491s) hardware is designed to work with specific word sizes. . And finally,

### 13: Don't start a number with 0 [8:14](https://www.youtube.com/watch?v=63zGtiv89bA&t=494s)

[8:16](https://www.youtube.com/watch?v=63zGtiv89bA&t=496s) we've reached the fact that inspired this video. You've probably seen those posts on the internet making fun of JavaScript's dynamic typing. One I've seen showed 010 double equals in
[8:26](https://www.youtube.com/watch?v=63zGtiv89bA&t=506s) quotations 8 as being true, commenting on how weird JavaScript is. But aside from the dynamic typing, this is also true in C. what's going on? Often you
[8:36](https://www.youtube.com/watch?v=63zGtiv89bA&t=516s) want to give numbers in specific base representations. You can do this using what's called a literal prefix. The most common is 0x for hexodimal. For example,
[8:46](https://www.youtube.com/watch?v=63zGtiv89bA&t=526s) 0x FF is 255. , we can also write numbers in octal, which is base 8. But for whatever reason, it was decided that the literal prefix for octal should just
[8:56](https://www.youtube.com/watch?v=63zGtiv89bA&t=536s) be a 0. when you have 0 1 0, it's interpreting that as 1 0 in base 8, which is equal to 8. The same literal
[9:05](https://www.youtube.com/watch?v=63zGtiv89bA&t=545s) prefix of just the zero has been carried over into JavaScript. Alrighty. , that's it for this deep dive into the C iceberg. Hopefully, you were able to
[9:13](https://www.youtube.com/watch?v=63zGtiv89bA&t=553s) learn something new. And , of course, there is much more that I could have covered. , if you have any fun facts about C, please leave them in the comments. If you made it this far into the video, you might be interested in
[9:22](https://www.youtube.com/watch?v=63zGtiv89bA&t=562s) this other video where I talk about easy args, which is a minimal argument parsing library in C. YouTube's recommendation algorithm thinks that you'll this other video on the
[9:30](https://www.youtube.com/watch?v=63zGtiv89bA&t=570s) screen. , make of that what you will. And if you want to see more content this in the future, feel free to subscribe.