import { createSlice } from '@reduxjs/toolkit'

const statsSlice = createSlice({
  name: 'stats',
  initialState: { summary: null, matches: null, status: 'idle', error: null },
  reducers: {
    setStatsLoading(state) {
      state.status = 'loading'
      state.error = null
    },
    setStats(state, action) {
      state.summary = action.payload.summary
      state.matches = action.payload.matches
      state.status = 'loaded'
      state.error = null
    },
    setStatsError(state, action) {
      state.status = 'error'
      state.error = action.payload
    },
  },
})

export const { setStatsLoading, setStats, setStatsError } = statsSlice.actions
export default statsSlice.reducer
