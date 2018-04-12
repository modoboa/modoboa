import Vue from 'vue'
import VueResource from 'vue-resource'

Vue.use(VueResource)

var domainResource = Vue.resource('/api/v1/domains{/pk}/')

export const getDomains = () => {
    return domainResource.get()
}

export const createDomain = (data) => {
    return domainResource.save(data)
}
