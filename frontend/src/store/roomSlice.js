import { createSlice } from '@reduxjs/toolkit'

const roomSlice = createSlice({
  name: 'room',
  initialState: { room: null, error: null },
  reducers: {
    setRoom(state, action) {
      state.room = action.payload
      state.error = null
    },
    setError(state, action) {
      state.error = action.payload
    },
    leaveRoom(state) {
      state.room = null
    },
  },
})

export const { setRoom, setError, leaveRoom } = roomSlice.actions
export default roomSlice.reducer
