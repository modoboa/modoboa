<template>
  <div id="app">
    <div class="container is-fluid">
      <div class="columns">
        <div class="column is-3">
          <aside class="menu">
            <p class="menu-label">
              Admin
            </p>
            <ul class="menu-list">
              <router-link tag="li" :to="{ name: 'DomainList' }">
                <a>Domains</a>
              </router-link>
              <router-link tag="li" :to="{ name: 'DomainList' }">
                <a><b-icon icon="account"></b-icon>Identities</a>
              </router-link>
              <router-link tag="li" :to="{ name: 'DomainList' }">
                <a>Logs</a>
              </router-link>
              <router-link tag="li" :to="{ name: 'DomainList' }">
                <a>Settings</a>
              </router-link>
            </ul>
          </aside>
        </div>
        <div class="column is-9">
          <router-view/>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
    name: 'App'
}
</script>
