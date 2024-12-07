# DPHS
Download from Python http.server

# Usage

###### Directory tree
├── a
├── b
├── c/
└── example_dir/
    ├── h
    ├── i
    └── j/
        └── k/
            └── l

### 1. Connect to your server
```
$ python DPHS/dphs.py 192.168.1.6:8000
Connecting to http://192.168.1.6:8000
Connected Successfully
> 
```

### 2. Show help
```
> help
```
All commands are **ls(l)**, **get(g)**, **cd**, **pwd**, **print(p)**, **help(h)** and **quit(q)**.
And you can use **\[cmd\] -h** to show help.
\*: l is the simplified version of ls. The same applies for other parentheses.

### 3. Operate

##### ls(l)
`ls` : list the files and directory of current directory.
**All content will be labeled with serial number in square brackets**.

\*: If your file just called \[1\], use \\\[1\] to replace it.
```
> ls
[1] a
[2] b
[3] c/
[4] example_dir/
> ls [4]
[1] h
[2] i
[3] j/
```

##### get(g)
`get`: Download a file or a whole directory.
Use **labels** such as \[1\]
```
> get [1]
Downloading a
Successfully saved to a
```
\*: Files larger than 1Mib will display a progress bar.

Downloading a directory recursively
```
> g -r [4]
Downloading example_dir
Downloading example_dir/h to example_dir/h
Downloading example_dir/i to example_dir/i
Downloading example_dir/j to example_dir/j
Downloading example_dir/j/k to example_dir/j/k
Downloading example_dir/j/k/l to example_dir/j/k/l
Successfully saved to example_dir
```
Show help
`> get -h`


##### cd
`cd` : Change directory
```
> cd [4]
> ls
[1] h
[2] i
[3] j/
```

##### pwd
`pwd` : Print working directory
```
> pwd
/example_dir
```

##### print(p)
`print` : Print a utf-8 file
```
> cd /
> p a
Hello, I'm file a.
> 
```

### 4. Quit
`quit` : Quit the program(Ctrl-D)


### 5. Modify the http.server
**<span style="color:red">It's optional but recommend.</span>**

**Python's http.server(/lib/python3.x/http/server.py) will use index.html to replace the page if it exists, which makes the server fail.**

So we find these code in server.py
```python3
for index in "index.html", "index.htm":
    index = os.path.join(path, index)
    if os.path.isfile(index):
    ¦   path = index
    ¦   break
    else:
    ¦   return self.list_directory(path)
```
Replace it with(Actually, it's just keeping the last line and decrease indent)
```python3
return self.list_directory(path)
```

###### Or you can use server.py of this repository
`python DPHS/server.py`

\*: It's modified from Python3.10 of Linux

