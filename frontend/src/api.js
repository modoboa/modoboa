import Vue from 'vue'
import VueResource from 'vue-resource'

Vue.use(VueResource)

var domainResource = Vue.resource('/api/v1/domains{/pk}/')

export const getDomains = () => {
    return domainResource.get()
}

export const createDomain = data => {
    return domainResource.save(data)
}

export const updateDomain = data => {
    return domainResource.update({ pk: data.pk }, data)
}

var customParametersActions = {
    applications: {method: 'GET', url: '/api/v1/parameters/applications/'},
    structure: {method: 'GET', url: '/api/v1/parameters/structure/'}
}
var parametersResource = Vue.resource(
    '/api/v1/parameters{/app}/', {}, customParametersActions)

export const getParametersForApplication = (app) => {
    return parametersResource.get({app: app})
}

export const getParametersApplications = () => {
    return parametersResource.applications()
}

export const getParametersStructure = (app) => {
    return parametersResource.structure({app: app})
}

export const saveParametersForApplication = (app, values) => {
    return parametersResource.update({app: app}, values)
}

var logResource = Vue.resource('/api/v1/logs{/pk}/')

export const getLogs = () => {
    return logResource.get()
}
