var app = angular.module('skyrimPackageManagerApp', []);

app.controller('DlCtrl', ['$scope', '$http', '$timeout', function ($scope, $http, $timeout) {
    (function poll() {
        $http.get('/downloading').success(function(data){
            $scope.downloading = data['active_downloads'];
        })
        $timeout(poll, 1000);
    })();

    $scope.cancel = function(id){
        $http.get('/cancel_download/' + id)
    }

}]);

app.controller('InfoCtrl', ['$scope', '$http', '$timeout', function ($scope, $http, $timeout) {
    (function poll() {
        $http.get('/heartbeat');
        $timeout(poll, 5000);
    })();

    var loadNxmData = function(){
        $http.get('/nxm').success(function(data){
            $scope.nxm = data;
        })
    };
    loadNxmData();

    $scope.updateSaveLocation = function() {
        $http({
            url: '/set_cfg',
            method:'POST',
            data: {save_location:$scope.cfg.save_location_edit},
        })
        .success(function(){
            $scope.cfg.save_location = $scope.cfg.save_location_edit
            $scope.saveloc_edit = false;
        });
    };

    $scope.updateUserPass = function() {
        $http.post('/set_cfg', {'user':$scope.cfg.user, 'password':$scope.cfg.password})
        .success(function(){
            $scope.userpasss_edit = false;
        });
    };

    $scope.register_nxm = function() {
        $http.get('/nxm/register').success(function(){
            loadNxmData();
        });
    };

    $http.get('/status').success(function(data){
        $scope.cfg = data;
        $scope.cfg.save_location_edit = data.save_location;
    })
}]);
