<template>
  <div>
    <div class="text-h5 ml-4">
      {{ $gettext('Contacts') }}
    </div>
    <ContactList @edit-category="openEditCategoryForm" />
    <v-dialog v-model="showCategoryForm" persistent max-width="800px">
      <CategoryForm
        :category="selectedCategory"
        @close="closeForm"
        @added="fetchCategories"
        @updated="fetchCategories"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useContactsStore, useLayoutStore } from '@/stores'
import contactsApi from '@/api/contacts'
import ContactList from '@/components/contacts/ContactList.vue'
import CategoryForm from '@/components/contacts/CategoryForm.vue'

const router = useRouter()
const route = useRoute()
const { $gettext } = useGettext()
const contactsStore = useContactsStore()
const layoutStore = useLayoutStore()

const categories = ref([])
const selectedCategory = ref(null)
const showCategoryForm = ref(false)

const leftMenuItems = computed(() => {
  const result = [
    {
      icon: 'mdi-contacts',
      text: $gettext('Contacts'),
      to: { name: 'ContactList' },
    },
    {
      text: $gettext('Categories'),
      subheader: true,
    },
  ]
  for (const category of categories.value) {
    result.push({
      icon: 'mdi-label',
      text: category.name,
      action: () => filterByCategory(category),
    })
  }
  result.push({
    icon: 'mdi-plus',
    text: $gettext('Add a category'),
    action: openCategoryForm,
  })
  return result
})

function openCategoryForm() {
  showCategoryForm.value = true
}

function openEditCategoryForm() {
  selectedCategory.value = contactsStore.currentCategory
  showCategoryForm.value = true
}

function closeForm() {
  selectedCategory.value = null
  showCategoryForm.value = false
}

function filterByCategory(category) {
  contactsStore.setCurrentCategory(category)
  router.push({
    name: 'ContactList',
    params: {
      category: category.name,
    },
  })
}

function fetchCategories() {
  return contactsApi.getCategories().then((resp) => {
    categories.value = resp.data
  })
}

fetchCategories()

watch(leftMenuItems, (value) => {
  layoutStore.setLeftMenuItems(value)
})
watch(categories, () => {
  if (route.params.category && !contactsStore.currentCategory) {
    contactsStore.setCurrentCategory(
      categories.value.find((item) => item.name === route.params.category)
    )
  }
})
</script>
