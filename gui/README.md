# Steps to develop the GUIs

1. Install Nodejs and npm.

```shell
sudo apt-get update
sudo apt-get install nodejs
sudo apt-get install npm
```

2. Configure Ubuntu to use `node` as an alias for `nodejs`.

```shell
sudo update-alternatives --install /usr/bin/node node /usr/bin/nodejs 10
```

3. Install npm dependencies.

```shell
cd gui
npm install
```

4. Install Flask.

```shell
sudo pip install flask
```

5. Install electron and GUI dependencies.

```shell
sudo npm install electron-prebuilt -g
sudo install jquery -g
```
