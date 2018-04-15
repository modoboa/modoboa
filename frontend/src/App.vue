<template>
  <div id="app">
    <div id="main-container" class="container is-fluid">
      <div class="columns">
        <div class="column is-2">
          <aside class="menu">
            <p class="menu-label">
            Admin
            </p>
            <ul class="menu-list">
              <router-link v-for="(item, index) in menu" :key="index" tag="li" :to="{ name: item.route }">
                <a><b-icon :icon="item.icon" size="is-large"></b-icon><br> {{ item.label }}</a>
              </router-link>
            </ul>
          </aside>
        </div>
        <div class="column is-10 app-content">
          <router-view/>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
    name: 'App',
    data () {
        return {
            menu: [{
                route: 'DomainList',
                icon: 'domain',
                label: 'Domains'
            }, {
                route: 'DomainList',
                icon: 'account',
                label: 'Identities'
            }, {
                route: 'DomainList',
                icon: 'database-search',
                label: 'Logs'
            }, {
                route: 'DomainList',
                icon: 'tune',
                label: 'Settings'
            }]
        }
    }
}
</script>

<style>
 #main-container {
     margin-top: 20px;
 }
 .app-content {
     background: #ECF0F3;
 }
 .menu-list {
     text-align: center;
 }
</style>
