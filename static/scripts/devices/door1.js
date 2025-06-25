var Door1 = (function () {
    'use strict';
    
    //Constructor
    function Door1( mqtt_publish_topic, state )
    {
        MqttDevice.call( this, mqtt_publish_topic, state );
    }
    
    Door1.prototype = Object.create( MqttDevice.prototype );
    Door1.prototype.constructor = Door1;

    return Door1;
})();
