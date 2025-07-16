var Switch = (function() {
    'use strict';

    //Constructor
    function Switch( mqtt_publish_topic, mqtt_subscribe_topic, state )
    {
        MqttDevice.call( this, mqtt_publish_topic, state, mqtt_subscribe_topic );
    }

    Switch.prototype = Object.create( MqttDevice.prototype );
    Switch.prototype.constructor = Switch;

    Switch.prototype.showDeviceCommands = false;

    Switch.prototype.sendCommand = function( command )
    {
        console.log( 'Switch will send command ', command );
        if( this.publisher )
        {
            var text = "";
            var topicSuffix = "";
            // Note: switch inputs are low positive as they come from an RPI i.e. 
            // a 1 means no signal in input, open relay at output, and a 0 means 
            // signal detected in input, close relay at output
            switch( command )
            {
                case "enable": 
                    text = "0";
                    topicSuffix = "/enable"
                    break;
                case "disable": 
                    text = "1";
                    topicSuffix = "/enable"
                    break;
                case "override": 
                    text = "0";
                    topicSuffix = "/override"
                    break;
                case "stop_override": 
                    text = "1";
                    topicSuffix = "/override"
                    break;
                case "report_status": 
                    topicSuffix = "/report_status"
                    break;
            }
            var message = new Paho.Message( text );
            message.destinationName = this.mqtt_subscribe_topic + topicSuffix;
            console.log( 'Switch sending topic: ' + message.destinationName + ', message: ', message.payloadString );
            this.publisher.send( message );
        }
    }

    return Switch;
})();