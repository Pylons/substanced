
buster.testCase('sdi.grid.remotemodel', {

    setUp: function () {

        // make a mock grid
        this.grid = {
            setData: sinon.spy(),
            onViewportChanged: {subscribe: sinon.spy()}
        };

        // make a mock Event
        window.Slick.Event = sinon.spy();

    },

    "can setup and teardown": function() {
        var grid = this.grid;

        var remote = new Slick.Data.SdiRemoteModel({
        });

        assert.equals(window.Slick.Event.callCount, 3);

        remote.init(grid);

        assert(grid.setData.calledWith({length: 0}));
        assert(grid.onViewportChanged.subscribe.called);

        remote.destroy();

    }


});

