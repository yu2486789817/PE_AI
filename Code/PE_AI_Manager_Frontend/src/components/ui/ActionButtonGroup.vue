<template>
  <div class="action-group">
    <slot />
  </div>
</template>

<style scoped>
.action-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
</style>
