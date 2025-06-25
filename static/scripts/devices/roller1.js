var Roller1 = (function () {
    'use strict';
    
    //Constructor
    function Roller1( mqtt_publish_topic, state )
    {
        //public properties
        MqttDevice.call( this, mqtt_publish_topic, state );
    }
    
    Roller1.prototype = Object.create( MqttDevice.prototype );
    Roller1.prototype.constructor = Roller1;

    return Roller1;
})();