let
  pkgs = import (fetchTarball ("channel:nixpkgs-unstable")) { };
in
pkgs.callPackage (
  { mkShell }:

  mkShell {
    strictDeps = true;

    # Инструменты разработки
    nativeBuildInputs = [
      pkgs.python312
      pkgs.python312Packages.pip
      pkgs.python312Packages.setuptools

      # строгая статическая типизация
      pkgs.pyright
      pkgs.python312Packages.mypy
      pkgs.ty

      # линтинг и дополнительные проверки
      pkgs.ruff
    ];

    buildInputs = [ ];

    # мне это пока не надо
    # shellHook = ''
    #   export PYTHONPATH=$PWD/src
    #   echo "Strict typed Python shell ready"
    #   python --version
    # '';
  }
) { }
