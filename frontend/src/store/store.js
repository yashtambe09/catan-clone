import { configureStore } from '@reduxjs/toolkit'
import connectionReducer from './connectionSlice'
import roomReducer from './roomSlice'

export const store = configureStore({
  reducer: {
    connection: connectionReducer,
    room: roomReducer,
  },
})
