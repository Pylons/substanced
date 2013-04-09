
var config = module.exports;

config["sdi.grid.remotemodel"] = {
    rootPath: "../../",
    environment: "browser",
    libs: [
        "dist/jquery.js"
    ],
    sources: [
        "js/sdi.grid.remotemodel.js"
    ],
    tests: [
        "js/buster-test/sdi.grid.remotemodel-test.js"
    ]
};
