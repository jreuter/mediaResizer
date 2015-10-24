# Steps to develop the GUIs

1. Install Nodejs and npm.

    sudo apt-get update
    sudo apt-get install nodejs
    sudo apt-get install npm

2. Configure Ubuntu to use `node` as an alias for `nodejs`.

    sudo update-alternatives --install /usr/bin/node node /usr/bin/nodejs 10

3. Install npm dependencies.

    cd gui
    npm install

4. Install Flask.

    sudo pip install flask

5. Install electron and GUI dependencies.

    sudo npm install electron-prebuilt -g
    sudo install jquery -g
