import { createSlice } from '@reduxjs/toolkit'

function loadStoredAuth() {
  try {
    const token = localStorage.getItem('catan_token')
    const username = localStorage.getItem('catan_username')
    const userId = localStorage.getItem('catan_user_id')
    if (token && username && userId) {
      return { token, username, userId: Number(userId) }
    }
  } catch {
    // localStorage unavailable - fall through to logged-out state
  }
  return { token: null, username: null, userId: null }
}

const authSlice = createSlice({
  name: 'auth',
  initialState: { ...loadStoredAuth(), error: null },
  reducers: {
    setCredentials(state, action) {
      const { token, username, userId } = action.payload
      state.token = token
      state.username = username
      state.userId = userId
      state.error = null
      try {
        localStorage.setItem('catan_token', token)
        localStorage.setItem('catan_username', username)
        localStorage.setItem('catan_user_id', String(userId))
      } catch {
        // best-effort persistence only
      }
    },
    setAuthError(state, action) {
      state.error = action.payload
    },
    logout(state) {
      state.token = null
      state.username = null
      state.userId = null
      try {
        localStorage.removeItem('catan_token')
        localStorage.removeItem('catan_username')
        localStorage.removeItem('catan_user_id')
      } catch {
        // best-effort cleanup only
      }
    },
  },
})

export const { setCredentials, setAuthError, logout } = authSlice.actions
export default authSlice.reducer
