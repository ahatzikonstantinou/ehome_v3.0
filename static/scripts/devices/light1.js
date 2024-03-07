var Light1 = (function () {
    'use strict';
    
    //Constructor
    function Light1( mqtt_publish_topic, mqtt_subscribe_topic, state )
    {
        //public properties
        MqttDevice.call( this, mqtt_publish_topic, state, mqtt_subscribe_topic );
    }
    
    Light1.prototype = Object.create( MqttDevice.prototype );
    Light1.prototype.constructor = Light1;

    Light1.prototype.switch = function( value )
    {
        console.log( 'Light1 will send value ', value, ' to topic ', this.mqtt_subscribe_topic );
        if( this.publisher )
        {
            var message = new Paho.MQTT.Message( value == 'ON' ? '1' : '0' );
            message.destinationName = this.mqtt_subscribe_topic ;
            console.log( 'Light1 sending message: ', message.payloadString );
            this.publisher.send( message );

            // this.state.main = value;//debugging
        }
    }

    Light1.prototype.sendCommand = function( command )
    {
        console.log( 'Light1 will send command ', command );
        if( this.publisher )
        {
            var text = "";
            switch( command )
            {
                case "calibrate": text = "l";
                    break;
                case "check": text = "c";
                    break;
                case "report": text = "r";
                    break;
                case "access-point": text = "w";
                    break;
                case "activate": text = "a";
                    break;
                case "deactivate": text = "d";
                    break;
            }
            var message = new Paho.MQTT.Message( text );
            message.destinationName = this.mqtt_subscribe_topic ;
            console.log( 'Light1 sending message: ', message.payloadString );
            this.publisher.send( message );
        }
    }

    return Light1;
})();
