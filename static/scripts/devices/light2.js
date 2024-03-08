var Light2 = (function() {
    'use strict';

    //Constructor
    function Light2( mqtt_publish_topic, mqtt_subscribe_topic, state )
    {
        //public properties
        MqttDevice.call( this, mqtt_publish_topic, state, mqtt_subscribe_topic );
    }
    
    Light2.prototype = Object.create( MqttDevice.prototype );
    Light2.prototype.constructor = Light2;

    Light2.prototype.showDeviceCommands = false;

    Light2.prototype.switchLeft = function( value )
    {
        console.log( 'Light2 will send value ', value, ' to topic ', this.mqtt_subscribe_topic );
        if( this.publisher )
        {
            var message = new Paho.Message( '{"left": "' + value + '"}' );
            message.destinationName = this.mqtt_subscribe_topic ;
            console.log( 'Light2 sending message: ', message );
            this.publisher.send( message );

            // this.state.left = value;//debugging
        }
    }

    Light2.prototype.switchRight = function( value )
    {
        console.log( 'Light2 will send value ', value, ' to topic ', this.mqtt_subscribe_topic );
        if( this.publisher )
        {
            var message = new Paho.Message( '{"right": "' + value + '"}' );
            message.destinationName = this.mqtt_subscribe_topic ;
            console.log( 'Light2 sending message: ', message );
            this.publisher.send( message );

            // this.state.right = value;//debugging
        }
    }

    return Light2;
})();