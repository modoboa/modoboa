<template>
<div>
  <v-text-field
    ref="input"
    v-model="input"
    outlined
    dense
    autocomplete="new-password"
    v-bind="$attrs"
    v-on="$listeners"
    @input="update"
    @keydown="onKeyDown"
    />
  <div class="menu"
       v-if="showMenu"
       :style="`width: ${width}px;`"
       >
    <v-list class="list">
      <v-list-item
        v-for="(domain, index) in filteredDomains"
        :key="index"
        @click="selectDomain(domain)"
        :class="selectionIndex === index ? 'selected' : ''"
        >
        <v-list-item-title>{{ domain.name }}</v-list-item-title>
      </v-list-item>
    </v-list>
  </div>
</div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  props: {
    value: String,
    allowAdd: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    ...mapGetters({
      domains: 'identities/domains'
    }),
    filteredDomains () {
      return this.domains.filter(domain => domain.name.startsWith(this.domainSearch))
    }
  },
  data () {
    return {
      domainSearch: '',
      input: this.value,
      selectionIndex: 0,
      showMenu: false,
      width: 500
    }
  },
  methods: {
    onKeyDown (e) {
      const keyCode = e.keyCode

      if (keyCode === 40 || keyCode === 34) {
        // on arrow down or page down
        if (!this.showMenu) {
          this.domainSearch = ''
          this.showMenu = true
        } else {
          this.increaseSelectionIndex()
        }
        e.preventDefault()
      } else if (keyCode === 38 || keyCode === 33) {
        // on arrow up or page up
        if (!this.showMenu) {
          this.domainSearch = ''
          this.showMenu = true
        } else {
          this.decreaseSelectionIndex()
        }
        e.preventDefault()
      } else if (keyCode === 13 || keyCode === 9) {
        // on enter or tab
        if (this.filteredDomains.length > 0) {
          this.selectDomain(this.filteredDomains[this.selectionIndex])
        } else if (this.allowAdd) {
          this.selectDomain()
        }
        e.preventDefault()
      } else if (keyCode === 27) {
        // on escape
        if (this.filteredDomains.length > 0) {
          this.showMenu = false
          e.preventDefault()
        }
      }
    },
    increaseSelectionIndex () {
      if (this.selectionIndex >= this.filteredDomains.length - 1) {
        this.selectionIndex = 0
      } else {
        this.selectionIndex += 1
      }
    },
    decreaseSelectionIndex () {
      if (this.selectionIndex <= 0) {
        this.selectionIndex = this.filteredDomains.length - 1
      } else {
        this.selectionIndex -= 1
      }
    },
    selectDomain (domain) {
      if (domain !== undefined) {
        this.input = this.input.split('@')[0] + '@' + domain.name
      }
      this.showMenu = false
      this.$emit('input', this.input)
      this.$emit('domain-selected')
    },
    update (value) {
      if (this.input.indexOf('@') !== -1) {
        this.domainSearch = this.input.split('@')[1]
        if (this.allowAdd) {
          this.showMenu = this.filteredDomains.length > 0
        } else {
          this.showMenu = true
        }
      } else {
        this.showMenu = false
      }
      this.$emit('input', this.input)
    },
    onResize () {
      this.updateMinWidthProperty()
    },
    updateMinWidthProperty () {
      this.width = this.$refs.input.$el.clientWidth
    },
    reset () {
      this.input = ''
      this.domainSearch = ''
    }
  },
  mounted () {
    // window.addEventListener('resize', this.onResize)
  },
  updated () {
    this.$nextTick(() => {
      this.updateMinWidthProperty()
    })
  },
  watch: {
    value (newValue) {
      this.input = newValue
    }
  }
}
</script>

<style scoped>
.menu {
  display: inline-block;
  position: fixed;
  margin-top: -20px;
  padding: 5px 0;
  box-shadow: 0 1px 5px 1px rgba(0,0,0,0.3);
  overflow-y: auto;
  overflow-x: hidden;
  contain: content;
  z-index: 99;
}

.list {
  width: 100%;
  height: 100%;
  font-size: 1.1em;
  overflow-x: hidden;
  padding: 0;
}

.selected {
  background-color: cornsilk;
}
</style>
