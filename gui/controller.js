var app = angular.module('skyrimPackageManagerApp', []);
app.controller('DlCtrl', ['$scope', '$http', '$timeout', function ($scope, $http, $timeout) {

    (function poll() {
        $http.get('/downloading').success(function(data){
            $scope.downloading = data['active_downloads'];
        })
        $timeout(poll, 1000);
    })();
}]);

app.controller('InfoCtrl', ['$scope', '$http', '$timeout', function ($scope, $http, $timeout) {
    $http.get('/status').success(function(data){
        $scope.data = data;
    })
}]);
