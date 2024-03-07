var MotionCameraPanTilt = (function () {
    'use strict';
    
    //Constructor
    function MotionCameraPanTilt( mqtt_publish_topic, mqtt_subscribe_topic, cameraId, videostream, state, detection )
    {
        MotionCamera.call( this, mqtt_publish_topic, mqtt_subscribe_topic, cameraId, videostream, state, detection );
    }

    MotionCameraPanTilt.prototype = Object.create( MotionCamera.prototype );
    MotionCameraPanTilt.prototype.constructor = MotionCameraPanTilt;

    MotionCameraPanTilt.prototype.up = function(){ this._cmd( 'up' ); }
    MotionCameraPanTilt.prototype.down = function(){ this._cmd( 'down' ); }
    MotionCameraPanTilt.prototype.left = function(){ this._cmd( 'left' ); }
    MotionCameraPanTilt.prototype.right = function(){ this._cmd( 'right' ); }
    MotionCameraPanTilt.prototype.stop = function(){ this._cmd( 'stop' ); }

    return MotionCameraPanTilt;
})();
