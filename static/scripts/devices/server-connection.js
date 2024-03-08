var ServerConnection = (function () {
    'use strict';
    
    //Constructor
    function ServerConnection( server, mqtt_publish_topic, mqtt_subscribe_topic, state )
    {
        MqttDevice.call( this, mqtt_publish_topic, state, mqtt_subscribe_topic );
        this.server = server;
    }
    
    ServerConnection.prototype = Object.create( MqttDevice.prototype );
    ServerConnection.prototype.constructor = ServerConnection;

    ServerConnection.prototype.update = function( topic, message )
    {
        if( topic == this.mqtt_subscribe_topic )
        {
            try
            {
                var data = angular.fromJson( message );
                // console.log( 'data: ',  data );
                this.state = data;
                this.lastUpdate = Date.now();

                this.server.connection.type = data.type;
                this.server.connection.connecting = false;
            }
            catch( error )
            {
                console.error( error );
            }
        }
    }

    ServerConnection.prototype.refresh = function()
    {
        console.log( 'will refresh the connection type' );
        if( this.publisher )
        {
            var message = new Paho.Message( "" );
            message.destinationName = this.mqtt_publish_topic ;
            console.log( 'ServerConnection sending message: ', message, ' with publisher: ', this.publisher );
            this.publisher.send( message );
        }
    }

    ServerConnection.prototype.disconnected = function()
    {
        this.server.connection.type = 'NOT_CONNECTED';
        this.server.connection.connecting = false;
    }

    ServerConnection.prototype.connecting = function()
    {
        this.server.connection.connecting = true;
    }

    ServerConnection.prototype.connected = function( type )
    {
        this.server.connection.type = type;
        this.server.connection.connecting = false;
    }

    return ServerConnection;
})();