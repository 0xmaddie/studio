## log
- [2024-01-19](./2024_01_19.md)

## sweetpea
```
        [A] %eval = A
        [A] %wrap = [[A]]
		
        [A] %loop = [[A] %loop] A]

[A] %jump B %mark = [[B] A]

     [A] [B] %cat = [A B]
       [A B] %div = [A] [B]
	   
     [A] [B] %alt = [(A | B)]
   [(A | B)] %sub = [A] [B]

        [A] %copy = [A] [A]
    [A] [A] %bind = [A]

         [A] %del =
             %new = [A]

    [A] [B] %swap = [B] [A]
	
%halt ends the computation unsuccessfully.

          (A | B) = A
          (A | B) = B

           [A] @B = [A]
```

## studio
the studio packages (python, javascript) implement basic stuff i want
in different environments, like the scripting language associated with
f15n etc
