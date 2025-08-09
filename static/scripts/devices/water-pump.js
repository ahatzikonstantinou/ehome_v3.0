var WaterPump = (function () {
    'use strict';
    
    //Constructor
    function WaterPump( mqtt_publish_topic, mqtt_subscribe_topic, state )
    {
        MqttDevice.call( this, mqtt_publish_topic, state, mqtt_subscribe_topic );
    }
    
    WaterPump.prototype = Object.create( MqttDevice.prototype );
    WaterPump.prototype.constructor = WaterPump;

    WaterPump.prototype.sendCommand = function( command )
    {
        console.log( 'WaterPump will send command ', command );
        if( this.publisher )
        {
            // Note: WaterPump inputs are low positive as they come from an RPI i.e. 
            // a 1 means no signal in input, open relay at output, and a 0 means 
            // signal detected in input, close relay at output
            var message = new Paho.Message( "" );
            message.destinationName = this.mqtt_subscribe_topic;
            console.log( 'WaterPump sending topic: ' + message.destinationName + ', message: ', message.payloadString );
            this.publisher.send( message );
        }
    }

    return WaterPump;
})();
