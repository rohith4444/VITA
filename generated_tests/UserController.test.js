// UserController.test.js

const UserController = require('./UserController');
const UserService = require('./UserService');

jest.mock('./UserService');

describe('UserController', () => {
  let userController;
  let mockUserService;

  beforeEach(() => {
    mockUserService = new UserService();
    userController = new UserController(mockUserService);
  });

  test('UT-001: Get User by ID', async () => {
    const userId = 'Predefined user ID';
    const userData = 'Predefined user data';
    mockUserService.findById.mockResolvedValue(userData);
    const result = await userController.getUser(userId);
    expect(result).toEqual(userData);
  });

  test('UT-002: Create New User', async () => {
    const userData = 'Predefined user data';
    mockUserService.create.mockResolvedValue(userData);
    const result = await userController.createUser(userData);
    expect(result).toEqual(userData);
  });

  test('UT-003: Update User', async () => {
    const userId = 'Predefined user ID';
    const userData = 'Predefined user data';
    const updatedData = 'Updated user data';
    mockUserService.update.mockResolvedValue(updatedData);
    const result = await userController.updateUser(userId, userData);
    expect(result).toEqual(updatedData);
  });
});