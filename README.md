Gallery2
========

The very unofficial PHP 7 fork.

by [Scott Smitelli](mailto:scott@smitelli.com) and the original Gallery2
authors.

This is a copy of the Gallery 2.3.2 (full) source code as it was released on
SourceForge in April 2012. It has been updated to install and run without major
errors under PHP 7.

I have not bumped the version number, because fundamentally this is not my
project and it seems like a whole lot of effort to do.

What should I expect?
---------------------

This code should install and run under PHP 7 without error. It should get all
the way through the installer, even with all optional modules selected, without
sending a single notice to the error log. It should be possible to add albums
and items, resize images, and access all pages of the admin area without error.

I have not exercised every dark corner of the codebase. I don't think any single
person ever can. Many of these modules don't work or make sense on the modern
web anymore.

Things changed
--------------

In no particular order...

* Use `__construct()` instead of the class name for constructor methods.
* Replace expressions with variables when passing by reference.
* Fix mismatches in passing by value/reference and vice-versa.
* Mark methods as `static` when appropriate.
* Fix up method arguments and defaults to satisfy LSP-related warnings.
* Replace `preg_replace()`/`e` with `preg_replace_callback()`.
* Add seemingly missing `include`/`require`s.
* Fix mistyped identifiers that were not case-sensitive before but now are.
* Fix `''` being sent to builtin functions that now expect `NULL`.
* Silence noise from expected-to-fail functions (like `is_uploaded_file()`).
* Add braces inside expressions like `$entity->{$callbacks[$i]}`.
* Update FFmpeg module with additional video types, and update the output parser
  to understand v3.x output.
* Update GD module to understand versions higher than 2.0.
* Remove several broken links in the KSIcons pack.
* Update ImageMagick module to understand v6 output.
* Update jpegtran module to understand new output.
* Add note about the piclens.com domain now being defunct.
* Several single occurrences of various programming errors.

All `MANIFEST` files have been rewritten to silence the installer warning about
modified files. A Python script that automatically does this has been added in
the `.fixers` directory should you wish to do the same.

So this software is maintained now, and secure?
-----------------------------------------------

Chortle.

Seriously, this software is _old_ and _abandoned_. I dragged it _kicking and
screaming_ into 2018 because I am a _stubborn idiot_. This is how I choose to
share my personal photos, and to me it is worth the effort and risk. I can't
make any of these decisions for you.

Having said that, if somebody points out a legitimate vulnerability that could
plausibly be fixed without staring any further into the gaping maw of this beast
than I already have, then sure, I'll try to patch it. But I'm not going to go
looking for trouble on my own.

How was this done?
------------------

I wrote a series of Python programs that parsed the PHP class/method structure
across all the source files and reported on things that were defined/called
incorrectly. I edited the offending source files and continued running the
parser programs until they no longer caught any errors. Then I tried installing
Gallery2 under php7-fpm and watched the error logs for new kinds of errors to
make the parser programs catch. Lather, rinse, repeat.

Is this really running somewhere?
---------------------------------

It most certainly is:
[https://gallery.scottsmitelli.com](https://gallery.scottsmitelli.com/)

As of this writing, the system information output is:

    ...
    PHP version = 7.0.30-0+deb9u1 fpm-fcgi
    Webserver = nginx/1.10.3
    Database = mysqli 5.5.5-10.1.26-MariaDB-0+deb9u1, lock.system=flock
    Toolkits = Thumbnail, Gd, ImageMagick, NetPBM, SquareThumb, Ffmpeg
    Acceleration = partial/3600, none/0
    Operating system = Linux [...] 4.17.17-x86_64-linode116 #1 SMP PREEMPT Mon Aug 20 16:07:40 UTC 2018 x86_64
    Default theme = matrix
    gettext = enabled
    Locale = en_US
    ...

License
-------

The original Gallery2 source is licensed as GPL version 2, and my modifications
are as well.
