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
    structure: {method: 'GET', url: '/api/v1/parameters/structure/'}
}
var parametersResource = Vue.resource('/api/v1/parameters/', {}, customParametersActions)

export const getParameters = () => {
    return parametersResource.get()
}

export const getParametersStructure = () => {
    return parametersResource.structure()
}
