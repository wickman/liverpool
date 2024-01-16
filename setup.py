from setuptools import setup, find_packages, Command


class RunTests(Command):
  user_options = []

  def initialize_options(self):
    pass

  def finalize_options(self):
    pass

  def run(self):
    import sys, subprocess
    errno = subprocess.call([sys.executable, '-m', 'unittest'])
    raise SystemExit(errno)


setup(
    name='liverpool',
    version='0.1.0',
    description='contract rummy algorithms',
    url='http://github.com/wickman/liverpool',
    author='Brian Wickman',
    author_email='wickman@gmail.com',
    license='MIT',
    packages=['liverpool', 'liverpool.bin'],
    zip_safe=True,
    cmdclass={'unittest': RunTests},
    entry_points = {
        'console_scripts': [
            'liverpool = liverpool.bin.play:cli'
        ]
    }
)
