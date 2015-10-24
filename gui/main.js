var app = require('app');
var BrowserWindow = require('browser-window');
require('crash-reporter').start();

var pjson = require('./package.json');

// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
var mainWindow = null;

// Quit when all windows are closed.
app.on('window-all-closed', function() {
    // On OS X it is common for applications and their menu bar
    // to stay active until the user quits explicitly with Cmd + Q
    if (process.platform != 'darwin') {
        app.quit();
    }
});

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
app.on('ready', function() {
    // call python
    var subpy = require('child_process').spawn('python', [__dirname + '/client.py']);

    // Create the browser window.
    mainWindow = new BrowserWindow({width: 800, height: 600});

    // Load the index.html.
    mainWindow.loadUrl('file://' + __dirname + '/index.html');

    // Open the devtools.
    if ( pjson.debug ) {
        mainWindow.webContents.openDevTools();
    }

    // Emitted when the window is closed.
    mainWindow.on('closed', function() {
        mainWindow = null;

        // Kill python.
        subpy.kill('SIGINT');
    });

});
