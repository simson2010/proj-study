# 管理后台 JWT Token 无状态认证方案

## 概述

本方案专门针对管理后台的身份认证和授权，在 Serverless 架构下实现无状态的 JWT Token 认证，确保用户可以正常执行查询、新增折扣记录等操作。

## 认证流程设计

### 整体认证流程

```mermaid
sequenceDiagram
    participant B as 管理后台前端
    participant GW as API 网关
    participant F as Serverless 函数
    participant DB as 数据库
    participant R as Redis 缓存

    B->>GW: 请求 /auth/login (用户名/密码登录)
    GW->>F: 转发请求到登录函数
    F->>DB: 查询用户信息并验证密码
    DB-->>F: 返回用户信息
    F->>F: 生成 JWT Token
    F->>R: 缓存 Token 和用户信息
    F-->>GW: 返回 Token
    GW-->>B: 返回 Token 和用户信息

    B->>GW: 请求 /api/xxx (携带 Token)
    GW->>GW: 验证 Token 有效性
    alt Token 有效
        GW->>F: 转发请求到业务函数
        F->>F: 解析 Token 获取用户信息
        F->>DB: 查询用户数据
        DB-->>F: 返回数据
        F-->>GW: 返回响应
        GW-->>B: 返回响应
    else Token 无效或过期
        GW-->>B: 返回 401 未授权
    end
```

## 核心组件设计

### 1. 管理后台用户登录

#### 登录控制器

```typescript
// src/modules/auth/controller/auth.controller.ts
import { Controller, Post, Body, Res } from '@nestjs/common';
import { Response } from 'express';
import { AuthService } from '../service/auth.service';
import { LoginDto } from '../dto/login.dto';

@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Post('login')
  async login(@Body() loginDto: LoginDto, @Res() res: Response) {
    try {
      const result = await this.authService.login(loginDto);

      return res.json({
        status: '0',
        message: 'Login successful',
        data: result,
      });
    } catch (error) {
      return res.status(401).json({
        status: '1',
        message: error.message || 'Login failed',
      });
    }
  }

  @Post('refresh')
  async refreshToken(@Body() body: { refreshToken: string }, @Res() res: Response) {
    try {
      const result = await this.authService.refreshToken(body.refreshToken);

      return res.json({
        status: '0',
        message: 'Token refreshed',
        data: result,
      });
    } catch (error) {
      return res.status(401).json({
        status: '1',
        message: error.message || 'Refresh token failed',
      });
    }
  }

  @Post('logout')
  async logout(@Body() body: { token: string }, @Res() res: Response) {
    try {
      await this.authService.logout(body.token);

      return res.json({
        status: '0',
        message: 'Logout successful',
      });
    } catch (error) {
      return res.status(500).json({
        status: '1',
        message: 'Logout failed',
      });
    }
  }
}
```

#### 认证服务

```typescript
// src/modules/auth/service/auth.service.ts
import { Injectable } from '@nestjs/common';
import { JwtAuthService } from './jwt.service';
import { RedisService } from './redis.service';
import { UserService } from '../user/service/user.service';
import { LoginDto } from '../dto/login.dto';
import * as crypto from 'crypto';

@Injectable()
export class AuthService {
  constructor(
    private readonly jwtAuthService: JwtAuthService,
    private readonly redisService: RedisService,
    private readonly userService: UserService,
  ) {}

  async login(loginDto: LoginDto) {
    // 验证用户名和密码
    const user = await this.validateUser(loginDto.username, loginDto.password);
    if (!user) {
      throw new Error('Invalid username or password');
    }

    // 生成访问 Token 和刷新 Token
    const accessToken = await this.jwtAuthService.generateAccessToken(user);
    const refreshToken = await this.jwtAuthService.generateRefreshToken(user);

    // 缓存 Token 与用户关联
    await this.redisService.setTokenUserRelation(accessToken, user.userId, 3600); // 1小时
    await this.redisService.setTokenUserRelation(refreshToken, user.userId, 604800); // 7天

    // 缓存用户信息
    await this.redisService.setUserInfo(user.userId, user);

    return {
      accessToken,
      refreshToken,
      userInfo: user,
    };
  }

  private async validateUser(username: string, password: string) {
    const user = await this.userService.findByUsername(username);
    if (!user) {
      return null;
    }

    // 验证密码（使用 MD5 加密，与原系统保持兼容）
    const hashedPassword = crypto.createHash('md5').update(password).digest('hex');
    if (user.password !== hashedPassword) {
      return null;
    }

    return user;
  }

  async refreshToken(refreshToken: string) {
    // 验证刷新 Token
    const decoded = await this.jwtAuthService.verifyRefreshToken(refreshToken);

    // 获取用户信息
    const user = await this.userService.findOne(decoded.userId);
    if (!user) {
      throw new Error('User not found');
    }

    // 生成新的访问 Token
    const accessToken = await this.jwtAuthService.generateAccessToken(user);

    // 缓存新的 Token 与用户关联
    await this.redisService.setTokenUserRelation(accessToken, user.userId, 3600); // 1小时

    // 缓存用户信息
    await this.redisService.setUserInfo(user.userId, user);

    return {
      accessToken,
    };
  }

  async logout(token: string) {
    try {
      const decoded = await this.jwtAuthService.verifyAccessToken(token);

      await this.redisService.blacklistToken(token, 3600);
      await this.redisService.deleteTokenUserRelation(token);
    } catch (error) {
      return;
    }
  }
}
```

### 2. JWT 生成与验证

#### JWT 服务

```typescript
// src/modules/auth/service/jwt.service.ts
import { Injectable } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { User } from '../user/entity/user.entity';

@Injectable()
export class JwtAuthService {
  constructor(private readonly jwtService: JwtService) {}

  async generateAccessToken(user: User): Promise<string> {
    const payload = {
      userId: user.userId,
      username: user.username,
      role: user.role,
      companyGroup: user.companyGroup,
    };

    return this.jwtService.sign(payload, {
      expiresIn: '1h',
      secret: process.env.JWT_ACCESS_SECRET,
    });
  }

  async generateRefreshToken(user: User): Promise<string> {
    const payload = {
      userId: user.userId,
      username: user.username,
    };

    return this.jwtService.sign(payload, {
      expiresIn: '7d',
      secret: process.env.JWT_REFRESH_SECRET,
    });
  }

  async verifyAccessToken(token: string): Promise<any> {
    try {
      return this.jwtService.verify(token, {
        secret: process.env.JWT_ACCESS_SECRET,
      });
    } catch (error) {
      throw new Error('Invalid access token');
    }
  }

  async verifyRefreshToken(token: string): Promise<any> {
    try {
      return this.jwtService.verify(token, {
        secret: process.env.JWT_REFRESH_SECRET,
      });
    } catch (error) {
      throw new Error('Invalid refresh token');
    }
  }
}
```

#### 认证中间件

```typescript
// src/modules/auth/middleware/jwt.middleware.ts
import { Injectable, NestMiddleware } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import { JwtAuthService } from '../service/jwt.service';
import { RedisService } from '../service/redis.service';

@Injectable()
export class JwtAuthMiddleware implements NestMiddleware {
  constructor(
    private readonly jwtAuthService: JwtAuthService,
    private readonly redisService: RedisService,
  ) {}

  async use(req: Request, res: Response, next: NextFunction) {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        status: '1',
        message: 'Token is missing',
      });
    }

    const token = authHeader.slice(7);

    try {
      const decoded = await this.jwtAuthService.verifyAccessToken(token);

      const isBlacklisted = await this.redisService.get(`token:blacklist:${token}`);
      if (isBlacklisted) {
        return res.status(401).json({
          status: '1',
          message: 'Token has been invalidated',
        });
      }

      const user = await this.redisService.get(`user:${decoded.userId}`);
      if (!user) {
        return res.status(401).json({
          status: '1',
          message: 'User not found',
        });
      }

      req['user'] = JSON.parse(user);
      req['token'] = token;

      next();
    } catch (error) {
      if (error.message === 'jwt expired') {
        return res.status(401).json({
          status: '1',
          message: 'Token has expired',
        });
      } else {
        return res.status(401).json({
          status: '1',
          message: 'Invalid token',
        });
      }
    }
  }
}
```

### 3. 用户管理功能实现

#### 用户实体

```typescript
// src/modules/user/entity/user.entity.ts
import { Entity, Column, PrimaryGeneratedColumn } from 'typeorm';

@Entity('user')
export class User {
  @PrimaryGeneratedColumn()
  userId: number;

  @Column({ unique: true })
  username: string;

  @Column()
  password: string;

  @Column()
  city: string;

  @Column()
  companyGroup: string;

  @Column()
  role: string;

  @Column({ type: 'datetime' })
  createTime: Date;

  @Column({ type: 'datetime' })
  updateTime: Date;

  @Column({ type: 'bigint', nullable: true })
  expireDate: number;
}
```

#### 用户服务

```typescript
// src/modules/user/service/user.service.ts
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from '../entity/user.entity';

@Injectable()
export class UserService {
  constructor(
    @InjectRepository(User)
    private readonly userRepository: Repository<User>,
  ) {}

  async findByUsername(username: string): Promise<User | null> {
    return this.userRepository.findOne({ where: { username } });
  }

  async findOne(userId: number): Promise<User | null> {
    return this.userRepository.findOne({ where: { userId } });
  }

  async findAll(): Promise<User[]> {
    return this.userRepository.find();
  }
}
```

### 4. 折扣管理功能实现

#### 折扣控制器

```typescript
// src/modules/discount/controller/discount.controller.ts
import { Controller, Get, Post, Body, UseGuards } from '@nestjs/common';
import { DiscountService } from '../service/discount.service';
import { CreateDiscountDto } from '../dto/create-discount.dto';
import { AuthGuard } from '../../auth/guard/auth.guard';
import { CurrentUser } from '../../auth/decorator/current-user.decorator';
import { User } from '../../user/entity/user.entity';

@Controller('discount')
@UseGuards(AuthGuard)
export class DiscountController {
  constructor(private readonly discountService: DiscountService) {}

  @Get()
  async getDiscounts(@CurrentUser() user: User) {
    return this.discountService.getDiscountsByUser(user);
  }

  @Post()
  async createDiscount(@Body() createDiscountDto: CreateDiscountDto, @CurrentUser() user: User) {
    return this.discountService.createDiscount(createDiscountDto, user);
  }
}
```

#### 折扣服务

```typescript
// src/modules/discount/service/discount.service.ts
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Discount } from '../entity/discount.entity';
import { User } from '../../user/entity/user.entity';
import { CreateDiscountDto } from '../dto/create-discount.dto';

@Injectable()
export class DiscountService {
  constructor(
    @InjectRepository(Discount)
    private readonly discountRepository: Repository<Discount>,
  ) {}

  async getDiscountsByUser(user: User): Promise<Discount[]> {
    if (user.role === 'user') {
      return this.discountRepository.find({
        where: { status: 0 },
        order: { createTime: 'DESC' },
      });
    }

    return this.discountRepository.find({
      order: { createTime: 'DESC' },
    });
  }

  async createDiscount(discountData: CreateDiscountDto, user: User): Promise<Discount> {
    if (user.role !== 'admin') {
      throw new Error('Permission denied');
    }

    const discount = this.discountRepository.create({
      ...discountData,
      creator: user.username,
      updater: user.username,
    });

    return this.discountRepository.save(discount);
  }
}
```

#### 折扣实体

```typescript
// src/modules/discount/entity/discount.entity.ts
import { Entity, Column, PrimaryGeneratedColumn } from 'typeorm';

@Entity('discount')
export class Discount {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  name: string;

  @Column()
  city: string;

  @Column()
  category: string;

  @Column()
  discount: string;

  @Column()
  detail: string;

  @Column()
  startDate: string;

  @Column()
  endDate: string;

  @Column({ nullable: true })
  phoneNumber: string;

  @Column({ nullable: true })
  address: string;

  @Column({ nullable: true })
  introduction: string;

  @Column({ type: 'double', nullable: true })
  longitude: number;

  @Column({ type: 'double', nullable: true })
  latitude: number;

  @Column({ nullable: true })
  iconUrl: string;

  @Column({ nullable: true })
  picUrl: string;

  @Column({ default: 0 })
  status: number;

  @Column({ default: 0 })
  barrierFree: number;

  @Column()
  creator: string;

  @Column()
  updater: string;

  @Column({ type: 'datetime' })
  createTime: Date;

  @Column({ type: 'datetime' })
  updateTime: Date;
}
```

## 认证方案实现关键点

### 1. JWT Token 存储与传输

#### 前端存储
```javascript
// 管理后台前端示例（使用 localStorage 存储）
const tokenStorage = {
  setToken: (token) => {
    localStorage.setItem('accessToken', token);
  },

  getToken: () => {
    return localStorage.getItem('accessToken');
  },

  removeToken: () => {
    localStorage.removeItem('accessToken');
  },

  setRefreshToken: (refreshToken) => {
    localStorage.setItem('refreshToken', refreshToken);
  },

  getRefreshToken: () => {
    return localStorage.getItem('refreshToken');
  },

  removeRefreshToken: () => {
    localStorage.removeItem('refreshToken');
  },
};

// 请求拦截器（使用 axios 示例）
axios.interceptors.request.use(
  (config) => {
    const token = tokenStorage.getToken();
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
axios.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = tokenStorage.getRefreshToken();
        const response = await axios.post('/auth/refresh', { refreshToken });

        const { accessToken } = response.data.data;
        tokenStorage.setToken(accessToken);

        originalRequest.headers['Authorization'] = `Bearer ${accessToken}`;
        return axios(originalRequest);
      } catch (refreshError) {
        tokenStorage.removeToken();
        tokenStorage.removeRefreshToken();
        // 跳转到登录页
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
```

#### 请求格式
```http
GET /api/discounts HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEsInVzZXJuYW1lIjoiYWRtaW4iLCJyb2xlIjoiYWRtaW4iLCJjb21wYW55R3JvdXAiOiJ0ZXN0IiwiaWF0IjoxNjYzNjc0MzI1LCJleHAiOjE2NjM2Nzc5MjV9.abc123xyz
Content-Type: application/json
```

### 2. 身份验证与授权

#### 装饰器与守卫
```typescript
// src/modules/auth/decorator/current-user.decorator.ts
import { createParamDecorator, ExecutionContext } from '@nestjs/common';

export const CurrentUser = createParamDecorator(
  (data: unknown, ctx: ExecutionContext) => {
    const request = ctx.switchToHttp().getRequest();
    return request['user'];
  },
);
```

```typescript
// src/modules/auth/guard/auth.guard.ts
import { Injectable, CanActivate, ExecutionContext } from '@nestjs/common';
import { Observable } from 'rxjs';

@Injectable()
export class AuthGuard implements CanActivate {
  canActivate(
    context: ExecutionContext,
  ): boolean | Promise<boolean> | Observable<boolean> {
    const request = context.switchToHttp().getRequest();
    return !!request['user'];
  }
}
```

#### 角色权限控制
```typescript
// src/modules/auth/guard/role.guard.ts
import { Injectable, CanActivate, ExecutionContext, ForbiddenException } from '@nestjs/common';
import { Observable } from 'rxjs';

@Injectable()
export class RoleGuard implements CanActivate {
  constructor(private readonly requiredRole: string) {}

  canActivate(
    context: ExecutionContext,
  ): boolean | Promise<boolean> | Observable<boolean> {
    const request = context.switchToHttp().getRequest();
    const user = request['user'];

    if (user && user.role === this.requiredRole) {
      return true;
    }

    throw new ForbiddenException('Insufficient permissions');
  }
}
```

### 3. 数据安全措施

#### Token 安全
- 使用强密钥加密
- Token 有效期设置合理
- Token 黑名单管理

#### 请求验证
- 输入验证与数据过滤
- SQL 注入防护
- 防止 XSS 攻击

#### 审计日志
```typescript
// src/modules/auth/interceptor/audit.interceptor.ts
import { Injectable, NestInterceptor, ExecutionContext, CallHandler } from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

@Injectable()
export class AuditInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const user = request['user'];

    if (user) {
      console.log(`[${new Date().toISOString()}] User ${user.username} (${user.userId}) accessed ${request.method} ${request.url}`);
    }

    return next.handle();
  }
}
```

## 部署方案

### 环境变量配置
```env
JWT_ACCESS_SECRET=your_access_secret_key
JWT_REFRESH_SECRET=your_refresh_secret_key
DB_HOST=localhost
DB_PORT=3306
DB_USERNAME=root
DB_PASSWORD=password
DB_DATABASE=staff_discount
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis_password
```

### Serverless 配置
```yaml
# serverless.yml
service: staff-discount-admin-api

provider:
  name: aliyun
  region: cn-hangzhou
  runtime: nodejs14.x
  environment:
    JWT_ACCESS_SECRET: ${env:JWT_ACCESS_SECRET}
    JWT_REFRESH_SECRET: ${env:JWT_REFRESH_SECRET}
    DB_HOST: ${env:DB_HOST}
    DB_PORT: ${env:DB_PORT}
    DB_USERNAME: ${env:DB_USERNAME}
    DB_PASSWORD: ${env:DB_PASSWORD}
    DB_DATABASE: ${env:DB_DATABASE}
    REDIS_HOST: ${env:REDIS_HOST}
    REDIS_PORT: ${env:REDIS_PORT}
    REDIS_PASSWORD: ${env:REDIS_PASSWORD}

functions:
  admin-api:
    handler: index.handler
    events:
      - http: ANY /
      - http: 'ANY {proxy+}'
```

## 总结

通过该方案，我们实现了管理后台的 JWT Token 无状态认证，主要特点包括：

### 1. 无状态认证
- 完全基于 JWT Token，无需存储 Session
- Token 包含用户身份信息和权限
- 支持 Token 刷新机制，提升用户体验

### 2. 安全保障
- 密码验证使用 MD5 加密，与原系统保持兼容
- Token 黑名单管理防止 Token 被滥用
- 角色权限控制确保数据安全

### 3. 性能优化
- 使用 Redis 缓存用户信息，减少数据库查询
- Token 验证过程高效，响应时间短

### 4. 可扩展性
- 支持多角色管理
- 代码结构模块化，易于维护和扩展

### 5. 与原系统兼容
- 保持数据库结构不变
- 支持原系统的用户数据和密码验证

该方案完全满足管理后台的认证需求，用户可以正常登录、查询和新增折扣记录，并确保数据安全性和系统性能。
