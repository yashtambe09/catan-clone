import { createSlice } from '@reduxjs/toolkit'

const connectionSlice = createSlice({
  name: 'connection',
  initialState: { status: 'disconnected' },
  reducers: {
    setStatus(state, action) {
      state.status = action.payload
    },
  },
})

export const { setStatus } = connectionSlice.actions
export default connectionSlice.reducer
