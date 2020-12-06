
from utz import *

DOCKERHUB_TOKEN_ENV = 'DOCKERHUB_TOKEN'
DOCKERHUB_USER_ENV = 'DOCKERHUB_USER'

def main(args=None):
    if lines('git','status','--short','--untracked-files','no'):
        raise RuntimeError('Found uncommitted changes; exiting')

    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-B','--no-branches',action='store_true',help="Don't tag image with branches pointing at current HEAD")
    parser.add_argument('-c','--copy',action='store_true',help='Copy src into built container (as opposed to cloning from GitHub')
    parser.add_argument('-j','--parallelism',help='Build parallelism during `docker build`')
    parser.add_argument('-l','--latest-only',action='store_true',help='Only create "latest" tag. By default, a tag for the python version is also created, as well as for the current Git commit (if there are no uncommitted changes)')
    parser.add_argument('-P','--push',action='store_true',help='Push built images')
    parser.add_argument('-r','--release',help='FFmpeg release to build (downloads source release directly by version, instead of cloning repo')
    parser.add_argument('--ref',help='Git SHA, branch, or tag to checkout in FFmpeg clone when building Docker image')
    parser.add_argument('-R','--clone-release-tag',help='When running against a release tag (e.g. n4.3.1), clone and release from the repo as opposed to defaulting to the released tar.bz2')
    parser.add_argument('-S','--no-sha',action='store_true',help="Don't tag image with current HEAD commit SHA")
    parser.add_argument('-t','--token',help='Token to log in to Docker Hub with')
    parser.add_argument('-T','--no-tags',action='store_true',help="Don't tag image with tags pointing at current HEAD")
    parser.add_argument('--token-env',default=DOCKERHUB_TOKEN_ENV,help=f'Environment variable storing a Docker Hub token (default: {DOCKERHUB_TOKEN_ENV})')
    parser.add_argument('-u','--username',help='User to log in to Docker Hub as')
    parser.add_argument('--username-env',default=DOCKERHUB_USER_ENV,help=f'Environment variable storing a Docker Hub username (default: {DOCKERHUB_USER_ENV})')
    parser.add_argument('--repository',help='Docker repository for built image')
    args = parser.parse_args(args)
    copy = args.copy
    latest_only = args.latest_only
    parallelism = args.parallelism
    push = args.push
    ref = args.ref
    release = args.release
    clone_release_tag = args.clone_release_tag
    tag_sha = not args.no_sha
    tag_tags = not args.no_tags
    tag_branches = not args.no_branches
    repository = args.repository
    if not repository:
        remotes = lines('git','remote')
        if len(remotes) == 1:
            [remote] = remotes
        elif not remotes:
            raise RuntimeError('No "repository" or git remotes found')
        else:
            if 'origin' in remotes:
                remote = 'origin'
            else:
                raise RuntimeError('No "origin" remote found; unsure which of %d candidates to choose: %s' % (len(remotes), str(remotes)))
        url = line('git','remote','get-url',remote)
        HTTPS_URL_REGEX = r'^https://github\.com/(?P<org>[^/]+)/(?P<repo>.+?)(?:.git)?$'
        SSH_URL_REGEX = r'git@github\.com:(?P<org>[^/]+)/(?P<repo>.+?)(?:.git)?$'
        if (m := match(HTTPS_URL_REGEX, url)) or (m := match(SSH_URL_REGEX, url)):
            repository = f'{m["org"]}/{m["repo"]}'.lower()
        else:
            raise RuntimeError(f'Unrecognized origin URL: {url}')

    token = args.token or env.get(args.token_env)
    username = args.username or env.get(args.username_env)
    if push and not (token and username):
        raise RuntimeError('-u/--username and -t/--token required in order to -p/--push (%s, %s)' % (username, token))

    if (copy or ref) and release:
        raise ValueError(f'-r/--release (building from a source release) is exclusive with --copy and/or --ref (copying/cloning source into image)')

    ref = ref or 'HEAD'
    sha = line('git','log','-n','1','--format=%H', ref)

    tags = lines('git','tag','--points-at',ref)
    release_tags = [ m['version'] for t in tags if (m := match('^n(?P<version>\d+\.\d+\.\d+)$', t)) ]
    if len(release_tags) > 1:
        raise RuntimeError('Multiple release tags found at commit %s: %s' % (sha, str(release_tags)))
    if release_tags:
        [release_tag] = release_tags
    else:
        release_tag = None

    if release_tag and not clone_release_tag:
        release = release_tag

    def _push(url):
        if push:
            run('docker','login','-u',username,'-p',token)
            run('docker','push',url)

    if copy:
        ctx = nullcontext()
        dir = None
    else:
        ctx = TemporaryDirectory()
        dir = ctx.name

    with ctx:
        file = docker.File(extend='Dockerfile.base', dir=dir)
        with use(file), file:
            configure = ' '.join([
                'PATH="$HOME/bin:$PATH" PKG_CONFIG_PATH="$HOME/ffmpeg_build/lib/pkgconfig"',
                './configure',
                '--prefix="$HOME/ffmpeg_build"',
                '--pkg-config-flags="--static"',
                '--extra-cflags="-I$HOME/ffmpeg_build/include"',
                '--extra-ldflags="-L$HOME/ffmpeg_build/lib"',
                '--extra-libs="-lpthread -lm"',
                '--bindir="$HOME/bin"',
                '--enable-gpl',
                '--enable-gnutls',
                '--enable-libaom',
                '--enable-libass',
                '--enable-libfdk-aac',
                '--enable-libfreetype',
                '--enable-libmp3lame',
                '--enable-libopus',
                '--enable-libvorbis',
                '--enable-libvpx',
                '--enable-libx264',
                '--enable-libx265',
                '--enable-nonfree',
            ])
            make = f'PATH="$HOME/bin:$PATH" make -j ${parallelism}'

            src_cmds = []

            if release:
                print(f'Building from source release {release}')
                name = f'ffmpeg-{release}'
                src_cmds = [
                    f'wget https://ffmpeg.org/releases/{name}.tar.bz2',
                    f'tar xjvf {name}.tar.bz2',
                    f'cd {name}',
                ]
            elif copy:
                print('Copying current clone into Docker')
                # copy current src into image
                COPY('.','FFmpeg')
                WORKDIR('/FFmpeg')
                if ref:
                    src_cmds = ['git','checkout',ref]
            else:
                print('Cloning FFmpeg from GitHub')
                src_cmds = [
                    'git clone https://github.com/FFmpeg/FFmpeg.git',
                    'cd FFmpeg',
                ]
                if ref:
                    src_cmds += [
                        f'git checkout {ref}',
                    ]

            RUN(
                *src_cmds,
                configure,
                make,
                'make install',
            )
            ENV(PATH="/root/bin:$PATH")
            ENTRYPOINT('["ffmpeg"]')

            file.build(repository)
    _push(repository)

    def tag(tg):
        url = f'{repository}:{tg}'
        if not latest_only:
            run('docker','tag',repository,url)
            _push(url)

    if release:
        tag(release)
    else:
        if tag_sha:
            tag(sha)

        if tag_tags:
            for t in tags:
                if (m := match('^n(?P<version>\d+\.\d+\.\d+)$', t)):
                    version = m['version']
                    print(f'Tagging release {version} from tag {t}')
                    tag(version)
                else:
                    tag(t)

        if tag_branches:
            branch_lines = lines('git','show-ref','--heads', err_ok=True) or []
            for ln in branch_lines:
                [branch_sha, branch_ref] = ln.split(' ', 2)
                if branch_sha == sha:
                    if (m := match('^refs/heads/(?P<branch>.*)', branch_ref)):
                        branch = m['branch']
                        tag(branch)


if __name__ == '__main__':
    main()
