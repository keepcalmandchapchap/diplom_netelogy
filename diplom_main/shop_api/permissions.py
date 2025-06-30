from rest_framework import permissions


class IsUserOrStaff(permissions.BasePermission):
    '''
    Проверяет, пользователь или менеджер
    '''
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or obj.user.is_staff
    def has_permission(self, request, view):
        return True
    
class IsUserOrInGroup(permissions.BasePermission):
    '''Проверка, обычный пользователь или определенные группы'''
    def __init__(self, groups=None):
        self.groups = groups

    def has_object_permission(self, request, view, obj):
        return request.user.groups.filter(name__in=self.group).exists() or obj.user == request.user

    def has_permission(self, request, view):
        return True

class IsInGroups(permissions.BasePermission):
    def  __init__(self, group=None):
        self.group = group or []

    def has_permission(self, request, view):
        return request.user.groups.filter(name__in=self.group).exists()
    
class IsVendorOrManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name__in=['manager_base', 'vendor_base']).exists()