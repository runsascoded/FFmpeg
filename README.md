# FFmpeg-docker README
(see [below](#original-readme) for the regular FFmpeg README)

This FFmpeg fork uses GitHub Actions to build [FFmpeg](https://ffmpeg.org) from source (both from published release `tar.bz2`s as well as arbitrary Git commits/branches) inside Docker images which are published to [the runsascoded/ffmpeg Docker Hub repository](https://hub.docker.com/repository/docker/runsascoded/ffmpeg). The latest release is [4.3.1](https://hub.docker.com/layers/129009716/runsascoded/ffmpeg/4.3.1/images/sha256-c75b6c176f02b7180362c85b05792db6b33d020b61b3e1143d822d3d3d55c982).

## Run `ffmpeg` without installing `ffmpeg`
```bash
docker run runsascoded/ffmpeg -version
# ffmpeg version 4.3.1 Copyright (c) 2000-2020 the FFmpeg developers
# built with gcc 8 (Debian 8.3.0-6)
# configuration: --prefix=/root/ffmpeg_build --pkg-config-flags=--static --extra-cflags=-I/root/ffmpeg_build/include --extra-ldflags=-L/root/ffmpeg_build/lib --extra-libs='-lpthread -lm' --bindir=/root/bin --enable-gpl --enable-gnutls --enable-libaom --enable-libass --enable-libfreetype --enable-libmp3lame --enable-libopus --enable-libvorbis --enable-libvpx --enable-libx264 --enable-libx265
# libavutil      56. 51.100 / 56. 51.100
# libavcodec     58. 91.100 / 58. 91.100
# libavformat    58. 45.100 / 58. 45.100
# libavdevice    58. 10.100 / 58. 10.100
# libavfilter     7. 85.100 /  7. 85.100
# libswscale      5.  7.100 /  5.  7.100
# libswresample   3.  7.100 /  3.  7.100
# libpostproc    55.  7.100 / 55.  7.100
```
These Docker images give you access to specific `ffmpeg` releases, built in [GitHub Actions that you can audit](https://github.com/runsascoded/FFmpeg/runs/1511352564?check_suite_focus=true#step:8:15673).

## Passing arguments
Any arguments you'd normally pass to `ffmpeg` can be sent to `docker run runsascoded/ffmpeg` instead.

However, input and output paths must additionally be mounted into the container. For example, if your inputs and outputs are in your current directory (`$PWD`), you can just mount it in (here to `/mnt`, and setting that as the working directory inside the container):
```bash
# down-sample `./my_video.mp4` to 10Mbps
docker run -v "$PWD:/mnt" -w /mnt runsascoded/ffmpeg -i my_video.mp4 -b:v 10M my_video_10M.mp4
```
This is analogous to the undockerized `ffmpeg` command:
```bash
ffmpeg -i my_video.mp4 -b:v 10M my_video_10M.mp4
```

If you run it this way frequently (operating on paths in the current directory), you could define a bash `ffmpeg` function to abstract the boilerplate away:
```bash
ffmpeg() {
  docker run -v "$PWD:/mnt" -w /mnt runsascoded/ffmpeg "$@"
}
```
then pretend you're running a locally-installed `ffmpeg`, as above:
```bash
ffmpeg -i my_video.mp4 -b:v 10M my_video_10M.mp4
```

## Source
- the default "docker" branch in this repo includes [relevant changes](https://github.com/FFmpeg/FFmpeg/compare/530d1dbcef...runsascoded:docker)
- example: [GitHub Actions workflow](https://github.com/runsascoded/FFmpeg/runs/1511352564) building+publishing [the version 4.3.1 image](https://hub.docker.com/layers/129009716/runsascoded/ffmpeg/4.3.1/images/sha256-c75b6c176f02b7180362c85b05792db6b33d020b61b3e1143d822d3d3d55c982)

--------

FFmpeg README <a id="original-readme"></a>
=============

FFmpeg is a collection of libraries and tools to process multimedia content
such as audio, video, subtitles and related metadata.

## Libraries

* `libavcodec` provides implementation of a wider range of codecs.
* `libavformat` implements streaming protocols, container formats and basic I/O access.
* `libavutil` includes hashers, decompressors and miscellaneous utility functions.
* `libavfilter` provides a mean to alter decoded Audio and Video through chain of filters.
* `libavdevice` provides an abstraction to access capture and playback devices.
* `libswresample` implements audio mixing and resampling routines.
* `libswscale` implements color conversion and scaling routines.

## Tools

* [ffmpeg](https://ffmpeg.org/ffmpeg.html) is a command line toolbox to
  manipulate, convert and stream multimedia content.
* [ffplay](https://ffmpeg.org/ffplay.html) is a minimalistic multimedia player.
* [ffprobe](https://ffmpeg.org/ffprobe.html) is a simple analysis tool to inspect
  multimedia content.
* Additional small tools such as `aviocat`, `ismindex` and `qt-faststart`.

## Documentation

The offline documentation is available in the **doc/** directory.

The online documentation is available in the main [website](https://ffmpeg.org)
and in the [wiki](https://trac.ffmpeg.org).

### Examples

Coding examples are available in the **doc/examples** directory.

## License

FFmpeg codebase is mainly LGPL-licensed with optional components licensed under
GPL. Please refer to the LICENSE file for detailed information.

## Contributing

Patches should be submitted to the ffmpeg-devel mailing list using
`git format-patch` or `git send-email`. Github pull requests should be
avoided because they are not part of our review process and will be ignored.
