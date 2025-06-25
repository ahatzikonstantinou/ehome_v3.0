var Door2R = (function () {
    'use strict';

    //Constructor
    function Door2R( mqtt_publish_topic, state )
    {
        //public properties
        MqttDevice.call( this, mqtt_publish_topic, state );
    }
    
    Door2R.prototype = Object.create( MqttDevice.prototype );
    Door2R.prototype.constructor = Door2R;

    return Door2R;
})();
