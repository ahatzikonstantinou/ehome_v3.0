var Alarm = (function() {
    'use strict';

    //Constructor
    function Alarm( mqtt_publish_topic, mqtt_subscribe_topic, state )
    {
        MqttDevice.call( this, mqtt_publish_topic, state, mqtt_subscribe_topic );
        this.showDeviceCommands = false;
    }
    Alarm.prototype = Object.create( MqttDevice.prototype );
    Alarm.prototype.constructor = Alarm;

    Alarm.prototype.setPublisher = function( publisher )
    {
        this.publisher = publisher;
    }

    Alarm.prototype.sendCommand = function( command )
    {
        console.log( 'Alarm will send command ', command );
        if( this.publisher )
        {
            var cmd = null;
            switch( command )
            {
                case "arm": cmd = {"command": "ARM_AWAY"};
                    break;
                case "arm_home": cmd = {"command": "ARM_HOME"};
                    break;
                case "disarm": cmd = {"command": "DISARM"};
                    break;
                case "sos": cmd = {"command": "SOS"};
                    break;
            }
            try
            {
                let message = new Paho.Message( JSON.stringify(cmd) );
                if(this.mqtt_subscribe_topic.trim().length == 0)
                {
                    throw new Error("Empty mqtt_subscribe_topic in Alarm device. Cannot send command.");
                }
                message.destinationName = this.mqtt_subscribe_topic ;
                console.log( 'Alarm sending topic: ' + message.destinationName + '  message: ', message.payloadString );
                this.publisher.send( message );
            }
            catch( error )
            {
                console.error( error );
            }
        }
    }
    
    return Alarm;
})();