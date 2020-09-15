Python argument parsing with log level and config file
======================================================

_Making use of `parse_known_args()` to set root log level and parse default values from a configuration file before parsing main args._

***

Suppose you're banging out a simple command-line utility in Python which has the following requirements:

1. Root log level can be set with a command-line argument
2. Configuration is _optionally_ read from an external file
3. Command-line arguments take precedence over configuration file

The `argparse.ArgumentParser` class includes the `parse_known_args()` method which allows for incrementally parsing the command-line arguments such that you can setup how subsequent arguments are parsed.


## Set log level from command-line argument

The root logger must be configured _before_ there is any output. If the argument parsing is going to be doing work that could or should produce log messages but you want the log level to be set from the arguments being parsed, use `parse_known_args()` to parse and set the log level first. Then proceed with the rest of the arguments.

[example.py gist](https://gist.github.com/MicahCarrick/8ded8859c82b2da1be9465d782fcfc04)

As an aside, I'm generally a fan of using [logging config files](https://docs.python.org/3/library/logging.config.html#logging-config-fileformat) to setup more robust logging for Python applications. However, for quick 'n simple command-line scripts I like the simplicity of this approach.


## Parse defaults from configuration file

A similar technique can be used to parse a configuration filename from the command-line arguments and then use that configuration file to set the default values for the remaining arguments being parsed.

Suppose a configuration file contains:

```
[options]
option1=config value
option2=config value
```

The way this works, is the default values for subsequent commmand-line arguments are defined in a dictionary named `defaults` rather than using the `default` keyword argument with `add_argument()`. Then, the `parse_known_args()` is used to parse the configuration filename from the command line arguments. If it is present then it reads the values out of the configuration and updates the `defaults` dictionary. Then those defaults are applied to the remaining command-line arguments with the `set_defaults()` method.

[example.py gist](https://gist.github.com/MicahCarrick/e050648f4f41e47e3ea4d58f1ce5501a)


## Putting it together

See the [complete example.py source code](https://github.com/MicahCarrick/micahcarrick-posts/blob/master/python-argparse-configfile-loglevel/example.py) which combines both of the above techniques.

Override default log level:

```
$ ./example.py -l DEBUG
INFO:__main__:Log level set: DEBUG
INFO:__main__:Option 1: default value
INFO:__main__:Option 2: default value
```

Read values from configuration file:

```
$ ./example.py -l DEBUG -c example.conf
INFO:__main__:Log level set: DEBUG
INFO:__main__:Loading configuration: example.conf
INFO:__main__:Option 1: config value
INFO:__main__:Option 2: config value
```

Override values with command-line arguments:

```
$ ./example.py -l DEBUG -c example.conf -1 "cli value"
INFO:__main__:Log level set: DEBUG
INFO:__main__:Loading configuration: example.conf
INFO:__main__:Option 1: cli value
INFO:__main__:Option 2: config value
```
